# Деплой Tender Intelligence Platform на Scalingo

[Scalingo](https://scalingo.com) — это европейская PaaS-платформа, полностью совместимая с экосистемой Heroku (поддерживает Buildpacks, Procfile, аддоны PostgreSQL/Redis и деплой через Docker).

Поскольку проект состоит из двух основных частей — **Python (FastAPI + Celery + Telegram Bot + Playwright)** и **Frontend (Vite / React)**, рекомендуется разделять деплой на два отдельных приложения в Scalingo. Это обеспечит независимое масштабирование, изоляцию ресурсов и максимальную производительность.

---

## Архитектура на Scalingo

1. **Приложение 1: `tender-backend` (Docker-деплой)**
   - **Процесс `web`**: FastAPI Web API и Admin Dashboard.
   - **Процесс `worker`**: Фоновые задачи Celery для парсинга и обработки.
   - **Процесс `beat`**: Celery Beat планировщик задач.
   - **Процесс `bot`**: Telegram бот (`aiogram`).
   - **Аддоны**: PostgreSQL и Redis.
2. **Приложение 2: `tender-frontend` (Static-деплой)**
   - Статическое SPA-приложение, скомпилированное из папки `frontend`, раздаваемое через быстрый CDN/Nginx.

---

## 🛠️ Шаг 1: Подготовка Backend к деплою

Скрейпинг сайтов (Playwright) требует наличия системных библиотек браузеров (GTK, GLib, NSS и др.). В стандартном Python buildpack их нет, поэтому **деплой бэкенда через Docker — это единственный надежный способ**.

Мы добавим файлы конфигурации Docker в корень вашего репозитория, чтобы Scalingo автоматически собрал и запустил проект.

### 1.1 Создание `Dockerfile` в корне проекта
В корневой директории репозитория создайте файл `Dockerfile` со следующим содержимым:

```dockerfile
FROM python:3.11-slim

# Установка системных зависимостей для сборки и curl
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Установка рабочей директории
WORKDIR /app

# Копирование и установка Python зависимостей
COPY backend_py/requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Установка браузера Chromium и системных зависимостей для Playwright
RUN playwright install chromium && \
    playwright install-deps chromium

# Копирование кода бэкенда
COPY backend_py/ .

# Создание необходимых директорий
RUN mkdir -p logs data

# Открытие порта для FastAPI
EXPOSE 8000

# Переменная окружения для корректного импорта модулей
ENV PYTHONPATH=/app

# Команда по умолчанию (будет переопределена в Procfile)
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### 1.2 Создание `Procfile` в корне проекта
Файл `Procfile` сообщает Scalingo, какие процессы нужно запустить внутри контейнера. Создайте в корневой директории файл `Procfile`:

```text
web: uvicorn app.main:app --host 0.0.0.0 --port $PORT
worker: celery -A app.workers.celery_app worker --loglevel=info
beat: celery -A app.workers.celery_app beat --loglevel=info
bot: python -m app.bot.bot
```

### 1.3 Создание `.dockerignore` в корне проекта
Исключите ненужные файлы из контекста сборки Docker, создав файл `.dockerignore`:

```text
.git
.env
node_modules
frontend
backend
logs
data
venv
```

---

## 💾 Шаг 2: Создание приложения бэкенда и баз данных

1. Войдите в панель управления [Scalingo Dashboard](https://my.scalingo.com).
2. Нажмите **Create a new app** и назовите его (например, `tender-backend`).
3. Перейдите во вкладку **Add-ons** созданного приложения:
   - Найдите и подключите **PostgreSQL** (план Starter или выше в зависимости от объемов данных).
   - Найдите и подключите **Redis** (используется как брокер для Celery и кэш).

---

## ⚙️ Шаг 3: Настройка переменных окружения

Перейдите во вкладку **Environment** вашего приложения `tender-backend` в панели Scalingo и добавьте следующие переменные:

| Переменная | Значение / Описание |
| :--- | :--- |
| `PYTHONPATH` | `/app` (Критически важно для работы импортов) |
| `DATABASE_URL` | Скопируйте значение из автоматически созданной переменной `SCALINGO_POSTGRESQL_URL`, заменив протокол на `postgresql+psycopg://...` (если требуется SQLAlchemy) |
| `REDIS_URL` | Скопируйте значение из переменной `SCALINGO_REDIS_URL` |
| `TELEGRAM_BOT_TOKEN` | Токен вашего бота от `@BotFather` |
| `TELEGRAM_ALERT_CHAT_ID` | ID канала или чата для отправки уведомлений (начинается с `-100`) |
| `TELEGRAM_API_ID` | API ID от [my.telegram.org](https://my.telegram.org) (для мониторинга каналов) |
| `TELEGRAM_API_HASH` | API Hash от [my.telegram.org](https://my.telegram.org) |
| `TELEGRAM_MONITOR_ENABLED` | `true` (если требуется мониторинг Telegram каналов через Telethon) |
| `GOOGLE_SERVICE_ACCOUNT_JSON` | JSON-ключ сервисного аккаунта Google Cloud (в одну строку) |
| `GOOGLE_SHEETS_SPREADSHEET_NAME` | Название вашей таблицы в Google Sheets |
| `GOOGLE_SHEETS_AUTO_EXPORT` | `true` |
| `SCRAPE_EVERY_MINUTES` | `15` (интервал парсинга) |
| `SCRAPE_HOUR` | `9` (час запуска парсинга по cron, по умолчанию 9) |
| `SCRAPE_MINUTE` | `0` (минута запуска парсинга по cron, по умолчанию 0) |

---

## 🚀 Шаг 4: Деплой Бэкенда

Вы можете настроить автодеплой при пуше в вашу ветку GitHub через панель Scalingo (раздел **Deployment -> Internet / GitHub**) или задеплоить вручную через Git:

```bash
# Установите Scalingo CLI (если еще не установлен)
# https://doc.scalingo.com/cli

# Авторизация в CLI
scalingo login

# Добавление удаленного репозитория Scalingo в ваш локальный Git
scalingo git:remote --app tender-backend

# Отправка кода на деплой
git add .
git commit -m "Configure Scalingo deployment"
git push scalingo main
```

Scalingo автоматически обнаружит `Dockerfile` в корне, соберет образ и подготовит его к запуску.

---

## 📈 Шаг 5: Масштабирование фоновых процессов

По умолчанию Scalingo запускает только процесс `web` (1 контейнер). Вам необходимо вручную активировать и масштабировать остальные процессы (`worker`, `beat`, `bot`).

Вы можете сделать это через Dashboard в разделе **Containers** или с помощью CLI:

```bash
# Запуск 1 контейнера для веб-сервера, воркера, планировщика и бота
scalingo --app tender-backend scale web:1 worker:1 beat:1 bot:1
```

*Примечание: Celery Beat (`beat`) строго должен быть запущен в единственном экземпляре (`beat:1`), иначе задачи будут дублироваться.*

---

## 🌐 Шаг 6: Деплой Frontend (React / Vite)

Для деплоя фронтенда создайте второе приложение на Scalingo, например, `tender-frontend`.

### 6.1 Настройка конфигурации сборки
В корневой папке `frontend` создайте файл `static.json` (или используйте настройки buildpack), чтобы настроить маршрутизацию для Single Page Application (SPA), избегая ошибок 404 при обновлении страниц:

```json
{
  "root": "dist",
  "routes": {
    "/**": "index.html"
  }
}
```

### 6.2 Переменные окружения фронтенда
В настройках приложения `tender-frontend` на Scalingo добавьте переменную окружения:

- `VITE_API_URL` = `https://tender-backend.scalingo.io` (URL вашего бэкенда на Scalingo).

### 6.3 Деплой фронтенда
Разверните фронтенд из подпапки. В Scalingo можно настроить **Monorepo** сборку, указав в настройках приложения (раздел **Deployment**) путь к директории сборки: `frontend`.

Или вручную из локальной папки:
```bash
# Инициализация Git внутри frontend, если это необходимо, либо пуш из монорепозитория
# Scalingo автоматически применит Node.js Buildpack, установит зависимости,
# выполнит `npm run build` и раздаст папку `dist`
```

---

## 🔍 Мониторинг и логирование на Scalingo

Следить за работой приложения можно прямо в терминале:

```bash
# Просмотр логов веб-сервера
scalingo --app tender-backend logs -p web

# Просмотр логов Celery воркера (парсеров)
scalingo --app tender-backend logs -p worker

# Просмотр логов Telegram бота
scalingo --app tender-backend logs -p bot

# Запуск миграций БД вручную (если необходимо)
scalingo --app tender-backend run alembic upgrade head

# Первоначальный сидинг ключевых слов в базу данных
scalingo --app tender-backend run python scripts/seed_keywords.py
```
