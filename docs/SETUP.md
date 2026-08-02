# Setup

## Prerequisites

- **Python 3.11+**
- **Node.js 18+** and npm
- A free **Adzuna API key** (for job discovery)
- *(optional)* an **Anthropic API key** — for higher-quality application answers

## 1. Get an Adzuna key (2 minutes, free)

1. Sign up at <https://developer.adzuna.com/>.
2. Confirm your email and open your dashboard.
3. Copy your **Application ID** and **Application Key**.

## 2. Configure `.env`

The launcher creates `.env` from `.env.example` on first run. Fill in:

```env
ADZUNA_APP_ID=your_app_id
ADZUNA_APP_KEY=your_app_key
ADZUNA_COUNTRY=in            # in, gb, us, ...

# Optional — better answers to "why should we hire you?" etc.
ANTHROPIC_API_KEY=

# Guardrails (defaults shown)
DAILY_COMPANY_LIMIT=10
FRESHNESS_DAYS=30
```

Without `ANTHROPIC_API_KEY`, application answers fall back to a resume-derived
template — the tool still works, the answers are just less polished.

## 3. Run

```bash
./scripts/run.sh
```

This installs dependencies, starts the backend (`:8000`) and frontend (`:5173`),
and opens the UI. Press **Ctrl+C** to stop.

## 4. Enable assisted apply (one-time)

The apply step drives a real browser via Playwright. Install its browser once:

```bash
cd backend
source .venv/bin/activate
playwright install chromium
```

When you click **Apply to selected**, a browser opens and auto-fills each
application from your resume. It pauses for the human-only steps — CAPTCHA,
review, and the final **Submit** — which you do yourself. It never submits on
its own.

## How the guardrails work

- **Freshness:** only openings created in the last `FRESHNESS_DAYS` days are
  shown, with the posting date on every card.
- **Daily budget:** discovery spends budget on at most `DAILY_COMPANY_LIMIT`
  new companies per calendar day; repeated searches accumulate toward the cap
  and it resets the next day.
- **Question memory:** an application question that isn't in your resume is
  asked once and remembered for 7 days.

## Troubleshooting

- **"Adzuna is not configured"** — fill `ADZUNA_APP_ID` / `ADZUNA_APP_KEY` in `.env`.
- **"Playwright is not installed"** — run the `playwright install chromium` step above.
- **No results** — broaden the role/location, or check that `ADZUNA_COUNTRY` matches where you're searching.
