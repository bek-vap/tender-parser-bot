@echo off
echo Starting Tender Intelligence Platform API Server...
echo.

cd /d "d:\My Projects\TENDER-INTELLIGENCE-PLATFORM\backend_py"

echo Setting Python path...
set PYTHONPATH=d:\My Projects\TENDER-INTELLIGENCE-PLATFORM\backend_py

echo Starting FastAPI server...
echo Server will run on: http://localhost:8000
echo Press Ctrl+C to stop the server
echo.

py -m uvicorn app.main:app --host 0.0.0.0 --port 8000
