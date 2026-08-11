# 🎯 Tender Intelligence Platform

An automated system that monitors public e-procurement (tender) platforms, filters new
tenders by keywords, and delivers matching results straight to Telegram — with winner
tracking, company enrichment, and one-click Excel / Google Sheets export. Built around a
**FastAPI** backend, a **Celery + Redis** task pipeline, **Playwright** scrapers, and a
**React** admin panel.

---

## ✨ Features

### Monitoring & filtering
- **Scheduled scraping** of multiple tender platforms on a daily / interval schedule
  (Celery beat).
- **Keyword filtering** — only tenders matching configured keywords are kept.
- **Anti-bot scraping** with Playwright + stealth for JavaScript-heavy sites.
- **Deduplication** so the same tender is never processed twice.

### Telegram delivery
- **Instant alerts** — each matching tender is sent to Telegram as a formatted card
  (title, budget, deadline, organizer, link).
- **Channel monitoring** via Telethon for tracking tender-related channels.

### Winner tracking & enrichment
- **Winner parser** — looks up who won a tender (company, price, organizer).
- **Company enrichment** — enriches organizations with extra data (e.g. tax ID).
- **Search by ID** — look up any tender or company by its identifier.

### Reporting
- **Excel export** (openpyxl) of tenders and winners.
- **Google Sheets export** (gspread) with automatic sync.

### Admin
- **React admin panel** to manage keywords, channels, monitored companies and trigger tasks.
- **REST API** (FastAPI) with per-feature routes and a health check.

---

## 🏗 Architecture

```
                ┌─────────────────┐
                │  React Admin UI │  (Vite + TypeScript)
                └────────┬────────┘
                         │ REST
                ┌────────▼────────┐        ┌──────────────┐
                │  FastAPI API    │◄──────►│  PostgreSQL  │  (SQLAlchemy + Alembic)
                └────────┬────────┘        └──────────────┘
                         │ enqueue
                ┌────────▼────────┐        ┌──────────────┐
                │  Celery workers │◄──────►│    Redis     │  (broker + schedule)
                │  + beat (cron)  │        └──────────────┘
                └────────┬────────┘
          ┌──────────────┼──────────────┬───────────────┐
          ▼              ▼              ▼               ▼
   Playwright       Keyword         Telegram        Excel /
   scrapers    →    filter     →    alerts     →    Sheets export
```

The API handles admin/config and on-demand actions; the heavy lifting (scraping, parsing,
alerting, exporting) runs asynchronously in Celery workers, scheduled by Celery beat.

---

## 🛠 Tech Stack

| Layer         | Technology |
|---------------|-----------|
| API           | FastAPI, Uvicorn, Pydantic Settings |
| Database      | PostgreSQL, SQLAlchemy 2.0, Alembic (migrations) |
| Task queue    | Celery + Redis (workers & scheduled beat) |
| Scraping      | Playwright + playwright-stealth, httpx |
| Telegram      | aiogram (bot), Telethon (channel monitoring) |
| Reporting     | openpyxl (Excel), gspread + google-auth (Google Sheets), pandas |
| Frontend      | React 18, Vite, TypeScript |
| Deployment    | Docker, Scalingo |

---

## 📁 Project Structure

```
.
├── backend_py/
│   └── app/
│       ├── api/routes/     # FastAPI endpoints (admin, keywords, winners, export, health…)
│       ├── scrapers/       # Platform scrapers (Playwright), sharing a common base
│       ├── services/       # Business logic (filter, winner parser, exports, alerts, CRM)
│       ├── clients/        # External API clients
│       ├── models/         # SQLAlchemy models (tender, winner, company, channel, admin…)
│       ├── workers/        # Celery app, scheduled tasks
│       ├── bot/            # Telegram bot
│       ├── db/             # Session / engine setup
│       ├── core/           # Config & settings
│       └── utils/          # Helpers
├── frontend/               # React + Vite admin panel
├── requirements.txt
├── Dockerfile
└── .env.example
```

---

## 🚀 Getting Started

### Prerequisites
- Python 3.12+
- PostgreSQL
- Redis
- Node.js (for the frontend)

### Backend

```bash
# 1. Clone
git clone https://github.com/bek-vap/tender-parser-bot.git
cd tender-parser-bot

# 2. Create a virtual environment & install deps
python -m venv venv
source venv/bin/activate            # Windows: venv\Scripts\activate
pip install -r requirements.txt

# 3. Install Playwright browsers
playwright install chromium

# 4. Configure environment
cp .env.example .env                # fill in your own values

# 5. Run database migrations
alembic upgrade head

# 6. Start the API
uvicorn app.main:app --reload       # run from backend_py/
```

### Background workers (in separate terminals)

```bash
# Celery worker
celery -A app.workers.celery_app worker --loglevel=info

# Celery beat (scheduler)
celery -A app.workers.celery_app beat --loglevel=info
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

### Configuration

All settings live in `.env` — see [`.env.example`](.env.example) for the full list
(database, Redis, Telegram bot token, Google Sheets, scraping schedule). **Never commit
your real `.env`** — only `.env.example` with placeholders is tracked.

---

## 📝 Notes

- Built as a real, end-to-end automation system: scheduled scraping, an async task
  pipeline, a relational data model with migrations, Telegram delivery, and reporting
  integrations.
- Secrets are kept out of version control via `.gitignore`; configuration is provided
  through environment variables.
