@echo off
REM Start Celery worker and beat for Tender Intelligence Platform (Windows)

echo Starting Celery worker and beat...

REM Kill any existing Celery processes
taskkill /f /im "celery.exe" 2>nul
timeout /t 2 /nobreak >nul

REM Start Celery worker in background
echo Starting Celery worker...
start /B celery -A app.workers.celery_app worker --loglevel=info

REM Wait a moment before starting beat
timeout /t 3 /nobreak >nul

REM Start Celery beat in background
echo Starting Celery beat...
start /B celery -A app.workers.celery_app beat --loglevel=info

echo Celery worker and beat started successfully!
echo Check logs with: celery -A app.workers.celery_app events
pause
