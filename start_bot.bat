@echo off
echo Starting Tender Intelligence Platform Bot...
echo.

cd /d "d:\My Projects\TENDER-INTELLIGENCE-PLATFORM\backend_py"

echo Setting Python path...
set PYTHONPATH=d:\My Projects\TENDER-INTELLIGENCE-PLATFORM\backend_py

echo Starting Telegram Bot...
echo Press Ctrl+C to stop the bot
echo.

py -m app.bot.bot
pause
