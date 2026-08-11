@echo off
echo Tender Intelligence Platform - API Server
echo ========================================

echo 1. Backend papkasiga o'tish...
cd /d "d:\My Projects\TENDER-INTELLIGENCE-PLATFORM\backend_py"

echo 2. PYTHONPATH o'rnatish...
set PYTHONPATH=d:\My Projects\TENDER-INTELLIGENCE-PLATFORM\backend_py

echo 3. API Server ishga tushurish...
echo    Host: 0.0.0.0
echo    Port: 8000
echo    Database: PostgreSQL (localhost:5400/tender)
echo.
echo API Documentation: http://localhost:8000/docs
echo.
echo Server ishga tushurilmoqda...
echo.

py -m uvicorn app.main:app --host 0.0.0.0 --port 8000

pause
