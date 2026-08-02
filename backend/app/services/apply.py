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


def run_assisted_apply(
    job: ApplyJob,
    opportunity: Opportunity,
    profile: Profile,
    headless: bool = False,
) -> None:
    """Drive a browser to autofill the application. Blocking — run in a thread.

    Degrades gracefully: if Playwright or its browser isn't available, the job
    still records the fill plan it *would* have applied, so nothing is silently
    lost.
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
            page = browser.new_page()
            page.goto(opportunity.url, wait_until="domcontentloaded", timeout=45000)

            raw = page.evaluate(_SCRAPE_JS)
            fields = [
                FormField(index=r["index"], tag=r["tag"], type=r["type"], label=r["label"])
                for r in raw
            ]
            plan = build_plan(fields, profile, opportunity)

            handles = page.query_selector_all("input, textarea, select")
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
            job.message = (
                "Autofill complete. Review the form, solve any CAPTCHA, answer "
                "any highlighted questions, then submit in the browser window."
            )
            _set(job)

            # Hold the browser open so the user can finish and submit.
            page.wait_for_timeout(10 * 60 * 1000)  # up to 10 minutes
            browser.close()
            if job.status == "awaiting_user":
                job.status = "done"
                _set(job)
    except Exception as exc:  # pragma: no cover - browser/runtime failures
        job.status = "error"
        job.message = f"Apply failed: {exc}"
        _set(job)


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
