Write-Host "=== Настройка Tender Intelligence Platform на Scalingo ===" -ForegroundColor Cyan

# 1. Проверка установки Scalingo CLI
if (-not (Get-Command scalingo -ErrorAction SilentlyContinue)) {
    Write-Host "[!] Scalingo CLI не найден в системе." -ForegroundColor Yellow
    Write-Host "[*] Устанавливаем Scalingo CLI..." -ForegroundColor Cyan
    iex (iwr -useb https://cli.scalingo.com/install.ps1)
    
    # Добавляем путь в текущую сессию
    $env:Path += ";$env:USERPROFILE\bin"
}

# 2. Авторизация
Write-Host "[*] Требуется авторизация в Scalingo. Пожалуйста, выполните вход в открывшемся окне..." -ForegroundColor Cyan
scalingo login

# Имя вашего приложения на Scalingo
$APP_NAME = "tender-backend"

# 3. Создание приложения
Write-Host "[*] Создаем приложение '$APP_NAME' на Scalingo..." -ForegroundColor Cyan
scalingo create $APP_NAME

# 4. Добавление аддонов (PostgreSQL и Redis)
Write-Host "[*] Добавляем базу данных PostgreSQL (план Starter 512MB)..." -ForegroundColor Cyan
scalingo --app $APP_NAME addons-add postgresql postgresql-starter-512

Write-Host "[*] Добавляем Redis (план Starter 256MB)..." -ForegroundColor Cyan
scalingo --app $APP_NAME addons-add redis redis-starter-256

# 5. Настройка переменных окружения
Write-Host "[*] Настраиваем переменные окружения..." -ForegroundColor Cyan
# Примечание: Переменные DATABASE_URL и REDIS_URL будут автоматически созданы аддонами.
# Пожалуйста, замените значения-заглушки реальными данными после выполнения скрипта
scalingo --app $APP_NAME env-set PYTHONPATH=/app `
    TELEGRAM_BOT_TOKEN="ВАШ_TELEGRAM_BOT_TOKEN" `
    TELEGRAM_ALERT_CHAT_ID="ВАШ_TELEGRAM_ALERT_CHAT_ID" `
    TELEGRAM_API_ID="ВАШ_TELEGRAM_API_ID" `
    TELEGRAM_API_HASH="ВАШ_TELEGRAM_API_HASH" `
    TELEGRAM_MONITOR_ENABLED="true" `
    GOOGLE_SHEETS_AUTO_EXPORT="true" `
    GOOGLE_SHEETS_SPREADSHEET_NAME="Tender Intelligence Platform" `
    SCRAPE_EVERY_MINUTES="15" `
    SCRAPE_HOUR="9" `
    SCRAPE_MINUTE="0"

# 6. Настройка Git Remote для Scalingo
Write-Host "[*] Подключаем Git remote для автоматического деплоя..." -ForegroundColor Cyan
scalingo git:remote --app $APP_NAME

Write-Host "`n=== 🎉 Успешно завершено! ===" -ForegroundColor Green
Write-Host "1. Отредактируйте переменные окружения в панели управления Scalingo (если не ввели их сразу)." -ForegroundColor Yellow
Write-Host "2. Для деплоя приложения выполните команду:" -ForegroundColor Yellow
Write-Host "   git push scalingo main" -ForegroundColor Cyan
Write-Host "3. После успешного деплоя запустите фоновые воркеры и ботов командой:" -ForegroundColor Yellow
Write-Host "   scalingo --app $APP_NAME scale web:1 worker:1 beat:1 bot:1" -ForegroundColor Cyan
