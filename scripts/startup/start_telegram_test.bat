@echo off
echo Testing Tender Intelligence Platform - Telegram Integration
echo.

cd /d "d:\My Projects\TENDER-INTELLIGENCE-PLATFORM\backend_py"

echo Setting Python path...
set PYTHONPATH=d:\My Projects\TENDER-INTELLIGENCE-PLATFORM\backend_py

echo Starting API server...
start "FastAPI Server" cmd /k py -m uvicorn app.main:app --host 0.0.0.0 --port 8000

echo.
echo API Server is starting on http://localhost:8000
echo.
echo Waiting 10 seconds for server to start...
timeout /t 10

echo.
echo Testing Telegram bot connection...
py -c "
from app.core.config import settings
from app.services.telegram_alerts import TelegramAlertService
import asyncio

async def test_telegram():
    try:
        bot = TelegramAlertService()
        await bot.bot.get_me()
        print('✅ Telegram bot connection successful!')
        print(f'Bot name: @{bot.bot.username}')
        print(f'Bot token configured: {bool(settings.TELEGRAM_BOT_TOKEN)}')
        print(f'Alert chat ID: {settings.TELEGRAM_ALERT_CHAT_ID}')
        return True
    except Exception as e:
        print(f'❌ Telegram bot connection failed: {e}')
        return False

result = asyncio.run(test_telegram())
if result:
    print('🎉 Telegram integration is working!')
else:
    print('❌ Telegram integration needs configuration')
"

echo.
echo Testing complete!
echo.
echo Next steps:
echo 1. Check API: http://localhost:8000/health
echo 2. Test endpoints: http://localhost:8000/docs
echo 3. Send test message to your bot
echo.
pause
