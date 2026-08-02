"""Assisted application engine.

Opens a job's application page in a real browser, auto-fills every field it
can from the resume and resolved answers, then hands control back to the user
for the human-only steps (CAPTCHA, review, final submit). It never clicks
submit on its own — that's a deliberate safety choice.

The fill *planning* (which field gets which value) is a pure function so it can
be unit-tested without a browser; the Playwright driving is layered on top.
"""
from __future__ import annotations

import threading
from dataclasses import dataclass, field
from typing import Callable, Optional

from ..models import Opportunity, Profile
from . import qa

# A field descriptor scraped from the page.
@dataclass
class FormField:
    index: int
    tag: str  # "input" | "textarea" | "select"
    type: str  # input type, e.g. "text", "email", "file"
    label: str  # best-guess human label


@dataclass
class FillAction:
    index: int
    label: str
    value: Optional[str]
    kind: str  # "text" | "essay" | "file"
    source: str  # profile | cache | resume | user | file
    needs_input: bool


def _kind_for(field: FormField) -> str:
    if field.type == "file":
        return "file"
    if field.tag == "textarea":
        return "essay"
    return "text"


def build_plan(
    fields: list[FormField],
    profile: Profile,
    opportunity: Optional[Opportunity] = None,
) -> list[FillAction]:
    """Decide what to type into each field. Pure — no browser involved."""
    actions: list[FillAction] = []
    for f in fields:
        kind = _kind_for(f)
        if kind == "file":
            actions.append(
                FillAction(
                    index=f.index,
                    label=f.label,
                    value=profile.resume_path,
                    kind="file",
                    source="file",
                    needs_input=profile.resume_path is None,
                )
            )
            continue
        res = qa.resolve(f.label, profile, opportunity)
        actions.append(
            FillAction(
                index=f.index,
                label=f.label,
                value=res.answer,
                kind=kind,
                source=res.source,
                needs_input=res.needs_input,
            )
        )
    return actions


# --- Job management --------------------------------------------------------

@dataclass
class ApplyJob:
    id: str
    opportunity_id: int
    status: str = "pending"  # pending | filling | awaiting_user | done | error
    message: str = ""
    plan: list[dict] = field(default_factory=list)
    pending_questions: list[str] = field(default_factory=list)


_JOBS: dict[str, ApplyJob] = {}
_LOCK = threading.Lock()


def get_job(job_id: str) -> Optional[ApplyJob]:
    with _LOCK:
        return _JOBS.get(job_id)


def _set(job: ApplyJob) -> None:
    with _LOCK:
        _JOBS[job.id] = job


# JS run in the page to enumerate fillable fields and their best-guess labels.
_SCRAPE_JS = r"""
() => {
  const out = [];
  const nodes = document.querySelectorAll('input, textarea, select');
  const skip = new Set(['hidden', 'submit', 'button', 'reset', 'checkbox', 'radio', 'image']);
  nodes.forEach((el, i) => {
    const type = (el.getAttribute('type') || (el.tagName === 'TEXTAREA' ? 'textarea' : 'text')).toLowerCase();
    if (skip.has(type)) return;
    let label = el.getAttribute('aria-label') || el.getAttribute('placeholder') || '';
    if (!label && el.id) {
      const lab = document.querySelector('label[for="' + CSS.escape(el.id) + '"]');
      if (lab) label = lab.innerText;
    }
    if (!label) {
      const parentLabel = el.closest('label');
      if (parentLabel) label = parentLabel.innerText;
    }
    if (!label) label = el.getAttribute('name') || '';
    out.push({ index: i, tag: el.tagName.toLowerCase(), type, label: (label || '').trim() });
  });
  return out;
}
"""


# LinkedIn "Apply" button selectors, most-specific first. On an external job the
# click opens the company portal (often in a new tab); we follow it.
_LINKEDIN_APPLY_SELECTORS = [
    "a[href*='externalApply']",
    "button.jobs-apply-button",
    "a.apply-button",
    "button[aria-label*='Apply' i]",
    "a:has-text('Apply on company website')",
    "button:has-text('Apply')",
    "a:has-text('Apply')",
]


def _resolve_linkedin(context, page):
    """From a LinkedIn job page, click Apply and follow to the company portal.

    Returns the page now showing the external application (a new tab or the
    same tab after navigation), or None if it stayed on LinkedIn — i.e. an
    Easy Apply modal or a login wall, which the user must handle manually.
    """
    for selector in _LINKEDIN_APPLY_SELECTORS:
        try:
            el = page.query_selector(selector)
        except Exception:
            el = None
        if el is None:
            continue
        # Case 1: opens the company portal in a new tab.
        try:
            with context.expect_page(timeout=8000) as popup_info:
                el.click()
            new_page = popup_info.value
            new_page.wait_for_load_state("domcontentloaded", timeout=25000)
            if "linkedin.com" not in new_page.url:
                return new_page
        except Exception:
            # Case 2: same-tab navigation to the portal.
            try:
                page.wait_for_load_state("domcontentloaded", timeout=15000)
            except Exception:
                pass
            if "linkedin.com" not in page.url:
                return page
    return None


def _drive(
    job: "ApplyJob",
    start_url: str,
    profile: Profile,
    opportunity: Optional[Opportunity],
    headless: bool = False,
) -> None:
    """Open a URL, follow a LinkedIn apply link to the company portal if needed,
    autofill the application, and pause for the human-only steps.

    Blocking — run in a thread. Degrades gracefully when Playwright or its
    browser is unavailable.
    """
    try:
        from playwright.sync_api import sync_playwright
    except Exception:
        job.status = "error"
        job.message = (
            "Playwright is not installed. Run `pip install playwright && "
            "playwright install chromium`."
        )
        _set(job)
        return

    job.status = "filling"
    _set(job)
    try:
        with sync_playwright() as pw:
            browser = pw.chromium.launch(headless=headless)
            context = browser.new_context()
            page = context.new_page()
            page.goto(start_url, wait_until="domcontentloaded", timeout=45000)

            target = page
            if "linkedin.com" in start_url:
                job.message = "Following the LinkedIn apply link to the company portal…"
                _set(job)
                resolved = _resolve_linkedin(context, page)
                if resolved is not None:
                    target = resolved
                else:
                    job.message = (
                        "Couldn't auto-open the company portal — this looks like "
                        "LinkedIn Easy Apply or a login wall. The page is open; "
                        "click Apply and complete it in the browser."
                    )
                    _set(job)

            raw = target.evaluate(_SCRAPE_JS)
            fields = [
                FormField(index=r["index"], tag=r["tag"], type=r["type"], label=r["label"])
                for r in raw
            ]
            plan = build_plan(fields, profile, opportunity)

            handles = target.query_selector_all("input, textarea, select")
            for action in plan:
                if action.index >= len(handles):
                    continue
                el = handles[action.index]
                try:
                    if action.kind == "file" and action.value:
                        el.set_input_files(action.value)
                    elif action.value and not action.needs_input:
                        el.fill(action.value)
                except Exception:
                    pass  # skip fields Playwright can't fill

            job.plan = [a.__dict__ for a in plan]
            job.pending_questions = [
                a.label for a in plan if a.needs_input and a.kind != "file"
            ]
            job.status = "awaiting_user"
            if not job.message or "click Apply" not in job.message:
                job.message = (
                    "Autofill complete. Review the form, solve any CAPTCHA, answer "
                    "any highlighted questions, then submit in the browser window."
                )
            _set(job)

            # Hold the browser open so the user can finish and submit.
            target.wait_for_timeout(10 * 60 * 1000)  # up to 10 minutes
            browser.close()
            if job.status == "awaiting_user":
                job.status = "done"
                _set(job)
    except Exception as exc:  # pragma: no cover - browser/runtime failures
        job.status = "error"
        job.message = f"Apply failed: {exc}"
        _set(job)


def run_assisted_apply(
    job: ApplyJob,
    opportunity: Opportunity,
    profile: Profile,
    headless: bool = False,
) -> None:
    """Autofill a stored opportunity's application page."""
    _drive(job, opportunity.url, profile, opportunity, headless)


def run_apply_url(
    job: ApplyJob,
    url: str,
    profile: Profile,
    headless: bool = False,
) -> None:
    """Autofill from an arbitrary job URL (LinkedIn link or a direct portal)."""
    _drive(job, url, profile, None, headless)


def start_apply(
    job_id: str,
    opportunity: Opportunity,
    profile: Profile,
    headless: bool = False,
) -> ApplyJob:
    job = ApplyJob(id=job_id, opportunity_id=getattr(opportunity, "id", 0) or 0)
    _set(job)
    thread = threading.Thread(
        target=run_assisted_apply,
        args=(job, opportunity, profile, headless),
        daemon=True,
    )
    thread.start()
    return job


def start_apply_url(
    job_id: str,
    url: str,
    profile: Profile,
    headless: bool = False,
) -> ApplyJob:
    job = ApplyJob(id=job_id, opportunity_id=0)
    _set(job)
    thread = threading.Thread(
        target=run_apply_url,
        args=(job, url, profile, headless),
        daemon=True,
    )
    thread.start()
    return job
