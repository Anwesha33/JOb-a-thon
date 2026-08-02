# JOb-a-thon

A personal job-hunt copilot. Point it at your resume and it will:

1. **Discover** recent openings (posted in the last month) from company career listings via the [Adzuna](https://developer.adzuna.com/) jobs API, matched to your resume.
2. **Shortlist** up to a list of companies for you to review — you pick which ones to apply to (or *Select all*), or narrow the search to specific companies you name.
3. **Apply** with an assisted browser that auto-fills each application from your resume and drafts answers to open questions ("Why should we hire you?" and friends) by pulling from your actual skills and experience.

It is deliberately **assisted**, not fully silent: the browser fills everything it can and pauses for the human-only bits (CAPTCHA, login, final submit). That keeps it reliable and keeps your accounts safe.

## Guardrails baked in

- **Freshness:** only openings created in the **last 30 days** are surfaced, and the posting date is shown on every card.
- **Daily budget:** discovery looks at at most **10 new companies per calendar day**, so you build a steady pipeline instead of a spammy blast.
- **Question memory:** if an application asks something that isn't in your resume, the tool asks you **once**, then remembers your answer for **7 days** so you're not retyping it.

## Layout

```
backend/    FastAPI service — discovery, matching, answer generation, apply engine
frontend/   React (Vite) UI — upload, review, select, apply
scripts/    One-command launcher
docs/       Setup notes (API keys, Playwright)
```

## Getting started

You'll need Python 3.11+, Node 18+, and a free [Adzuna API key](https://developer.adzuna.com/). Then:

```bash
./scripts/run.sh
```

This installs dependencies, starts the backend and frontend, and opens the UI at
<http://localhost:5173>. On first run it creates `.env` — add your Adzuna keys there.

Full instructions (API keys, enabling the Playwright browser for assisted apply,
troubleshooting) are in [`docs/SETUP.md`](docs/SETUP.md).

## How it works

1. **Upload** your resume — it's parsed into a profile (skills, contact, headline).
2. **Search** by role/location, optionally restricted to companies you name. Only
   openings from the last 30 days are surfaced, at most 10 new companies per day.
3. **Select** the ones you want (or *Select all*).
4. **Apply** — an assisted browser auto-fills each application from your resume and
   drafts answers to open questions; you handle CAPTCHA and the final submit. Any
   question it can't answer is asked once and remembered for a week.
