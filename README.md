# JOb-a-thon

A personal job-hunt copilot. Point it at your resume, and it finds recent
openings, lets you pick which ones to go after, and drives an assisted browser
that fills out each application for you.

```
resume  →  discover recent openings  →  you shortlist  →  assisted apply
```

## What it does

1. **Understands your resume.** Upload a PDF / DOCX / TXT and it extracts a
   profile — your contact details, headline, and skills — used to drive search
   and to answer application questions.
2. **Finds recent openings.** Searches the [Adzuna](https://developer.adzuna.com/)
   jobs API by role and location (or a specific list of companies you name), and
   shows a selectable list with the posting date on every card.
3. **Lets you choose.** Tick the openings you want, or **Select all**.
4. **Applies for you — assisted.** For each selected job it opens the application
   page, auto-fills fields from your resume, and drafts answers to open questions
   ("Why should we hire you?", strengths, etc.) grounded in your actual
   experience. It **pauses for the human-only steps** — CAPTCHA, login, and the
   final Submit — and **never submits on its own**. That keeps it reliable and
   your accounts safe.

### Guardrails baked in

- **Freshness** — only openings created in the last **30 days** are shown
  (`FRESHNESS_DAYS`), with the posting date on every card.
- **Daily budget** — discovery spends budget on at most **N new companies per
  calendar day** (`DAILY_COMPANY_LIMIT`, default 10). Repeated searches
  accumulate toward the cap; it resets the next day.
- **Question memory** — a question that isn't answerable from your resume is
  asked **once**, then remembered for **7 days** so you never retype it.

## Prerequisites

- **Python 3.11+**
- **Node.js 18+** and npm
- A free **Adzuna API key** — <https://developer.adzuna.com/> (30-second signup, no card)
- *(optional)* an **Anthropic API key** — sharper application answers; without it,
  answers fall back to a resume-derived template

## Setup

### 1. Clone

```bash
git clone https://github.com/Anwesha33/JOb-a-thon.git
cd JOb-a-thon
```

### 2. Get your Adzuna key

1. Sign up at <https://developer.adzuna.com/> and confirm your email.
2. Open <https://developer.adzuna.com/admin/access_details>.
3. Copy your **Application ID** and **Application Key**.

### 3. Run it

```bash
./scripts/run.sh
```

On the first run this:

- creates `.env` from `.env.example`,
- sets up the Python venv and installs backend + frontend dependencies,
- starts the backend (`:8000`) and frontend (`:5173`),
- opens the UI in your browser.

Press **Ctrl+C** to stop both.

### 4. Add your keys to `.env`

Edit `.env` (created in step 3) and fill in your Adzuna credentials:

```env
ADZUNA_APP_ID=your_app_id
ADZUNA_APP_KEY=your_app_key
ADZUNA_COUNTRY=in            # in, gb, us, ...

ANTHROPIC_API_KEY=           # optional
DAILY_COMPANY_LIMIT=10       # companies searched per day
FRESHNESS_DAYS=30            # only show postings this fresh
```

> The backend reads `.env` at startup, so **restart it** (Ctrl+C, then
> `./scripts/run.sh` again) after editing.

### 5. Enable assisted apply (one-time)

The apply step drives a real browser via Playwright. Install its browser once:

```bash
cd backend
source .venv/bin/activate
playwright install chromium
```

## Using it

Open <http://localhost:5173> and:

1. **Upload your resume.**
2. **Search** — enter a role and location (leave role blank to use your resume),
   and optionally list specific companies.
3. **Select** the openings you want, or **Select all**.
4. **Apply to selected** — a browser opens and auto-fills each application. If it
   hits a question it can't answer from your resume, a small dialog asks you once
   and remembers it for a week. Solve any CAPTCHA and click Submit yourself.

## Configuration

| Variable              | Default | Purpose                                            |
| --------------------- | ------- | -------------------------------------------------- |
| `ADZUNA_APP_ID`       | —       | Adzuna Application ID (required)                    |
| `ADZUNA_APP_KEY`      | —       | Adzuna Application Key (required)                   |
| `ADZUNA_COUNTRY`      | `in`    | Two-letter country for search (`in`, `gb`, `us`, …) |
| `ANTHROPIC_API_KEY`   | —       | Enables Claude-drafted answers (optional)          |
| `DAILY_COMPANY_LIMIT` | `10`    | Max new companies discovered per calendar day      |
| `FRESHNESS_DAYS`      | `30`    | Only surface postings created within this many days |

## Project structure

```
backend/    FastAPI service
  app/
    routers/     HTTP endpoints (resume, opportunities, answers, questions, apply)
    services/    discovery (Adzuna), throttle, parsing, answers, apply engine
    models.py    shared pydantic schemas
    db.py        SQLite storage
frontend/   React (Vite) UI — upload, search, select, apply
scripts/    run.sh — one-command launcher
docs/       SETUP.md — detailed setup + troubleshooting
```

## Tech stack

- **Backend:** FastAPI, SQLite, httpx (Adzuna), Playwright (assisted apply),
  the Anthropic SDK (optional answer generation).
- **Frontend:** React + Vite.

## Notes & limitations

- **Assisted, not silent.** Real career portals have logins, CAPTCHAs, and
  multi-step forms; fully hands-off mass-apply isn't reliable. This tool fills
  everything it can and hands you the last mile.
- **Adzuna is an aggregator.** It surfaces openings and links to each company's
  real application page — that link is what the apply engine drives.
- **Your data stays local.** The resume, parsed profile, discovered openings, and
  cached answers live in a local SQLite DB under `backend/data/`.

More detail (API keys, Playwright, troubleshooting) is in
[`docs/SETUP.md`](docs/SETUP.md).
