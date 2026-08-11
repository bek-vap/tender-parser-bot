@echo off
echo Starting PostgreSQL Database for Tender Intelligence Platform
echo.

echo Checking if PostgreSQL is running...
netstat -an | findstr ":5400" >nul
if %errorlevel% equ 0 (
    echo PostgreSQL is already running on port 5400
) else (
    echo Starting PostgreSQL...
    cd "C:\Program Files\PostgreSQL\16\bin"
    pg_ctl start -D "C:\Program Files\PostgreSQL\16\data"
    timeout /t 5
)

echo.
echo Database status check:
cd "C:\Program Files\PostgreSQL\16\bin"
pg_isready -h localhost -p 5400

if %errorlevel% equ 0 (
    echo PostgreSQL is running successfully!
) else (
    echo PostgreSQL failed to start
    echo Please check PostgreSQL installation
)

echo.
pause
