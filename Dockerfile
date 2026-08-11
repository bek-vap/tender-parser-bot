FROM python:3.11-slim

# Установка системных зависимостей
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Рабочая директория
WORKDIR /app

# Копирование и установка зависимостей бэкенда
COPY backend_py/requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Установка Playwright Chromium и необходимых системных библиотек
RUN playwright install chromium && \
    playwright install-deps chromium

# Копирование исходного кода бэкенда
COPY backend_py/ .

# Создание необходимых папок для рантайма
RUN mkdir -p logs data

# Порт веб-сервера
EXPOSE 8000

# Переменная окружения для корректной работы импортов
ENV PYTHONPATH=/app

# Command for production (Render.com):
# Set WEBHOOK_URL env var in Render dashboard to enable webhook mode.
# In webhook mode, you can increase workers safely.
# In polling mode (no WEBHOOK_URL), keep workers=1 to avoid TelegramConflictError.
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000} --workers 1"]
