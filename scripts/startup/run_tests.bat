@echo off
echo Testing Tender Intelligence Platform...
echo.

cd /d "d:\My Projects\TENDER-INTELLIGENCE-PLATFORM\backend_py"

echo Setting Python path...
set PYTHONPATH=d:\My Projects\TENDER-INTELLIGENCE-PLATFORM\backend_py

echo Testing database connection...
python -c "from app.db.session import SessionLocal; db = SessionLocal(); print(f'Database connected: {db.query(Keyword).count()} keywords'); db.close()"

echo.
echo Testing keyword matching...
python -c "from app.services.keyword_filter import KeywordFilterService; f = KeywordFilterService(); matches = f.match('строительство склад', [{'id': '1', 'phrase': 'строительство'}]); print(f'Keyword matching: {len(matches)} matches')"

echo.
echo Testing configuration...
python -c "from app.core.config import settings; print(f'Telegram bot configured: {bool(settings.TELEGRAM_BOT_TOKEN)}')"

echo.
echo Testing complete!
echo.
echo Next steps:
echo 1. Start API server: uvicorn app.main:app --host 0.0.0.0 --port 8000
echo 2. Test API: curl http://localhost:8000/health
echo 3. View docs: http://localhost:8000/docs
echo.
pause
