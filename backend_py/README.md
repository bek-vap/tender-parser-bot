# backend_py (Python stack)

Стек: FastAPI + Playwright + Celery + Redis + PostgreSQL + Aiogram.

## Переменные окружения

Создай `.env` в корне репозитория или в `backend_py/`:

```env
DATABASE_URL=postgresql+psycopg://postgres:postgres@localhost:5432/tender
REDIS_URL=redis://localhost:6379/0
TELEGRAM_BOT_TOKEN=123456:ABCDEF
TELEGRAM_ALERT_CHAT_ID=-1001234567890
UZEX_VALIDATION=PASTE_VALIDATION_HEADER_HERE
```

## Установка

```bash
cd backend_py
python -m venv .venv
# Windows:
.venv\\Scripts\\activate
pip install -r requirements.txt
playwright install chromium
```

## Инициализация БД (MVP)

Пока без Alembic можно создать таблицы через SQLAlchemy:

```bash
python -c "from app.db.init_db import init_db; init_db()"
```

## Запуск API

```bash
uvicorn app.main:app --reload --port 8000
```

## Запуск Celery worker

```bash
celery -A app.workers.celery_app.celery_app worker -l info
```

## Запуск Celery beat (планировщик каждые 15 минут)

```bash
celery -A app.workers.celery_app.celery_app beat -l info
```

## Запуск Telegram бота (команды/меню)

```bash
python -m app.bot.bot
```
