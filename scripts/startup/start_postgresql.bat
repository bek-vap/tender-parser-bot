@echo off
echo PostgreSQL ni ishga tushurish...
echo.

echo 1. PostgreSQL xizmatlarini tekshirish...
cd /d "C:\Program Files\PostgreSQL\18\bin"
pg_isready -h localhost -p 5432

if %errorlevel% equ 0 (
    echo PostgreSQL ishlatilgan bo'lishi kerak!
) else (
    echo PostgreSQL ishlatilmagan
    echo Xizmatni tekshiring...
    
    echo 2. PostgreSQL xizmatini o'rnatish...
    pg_ctl init -D "C:\Program Files\PostgreSQL\18\data"
    
    echo 3. PostgreSQL xizmatini boshlash...
    pg_ctl start -D "C:\Program Files\PostgreSQL\18\data"
    timeout /t 10
)

echo.
echo 4. PostgreSQL holatini tekshirish...
pg_isready -h localhost -p 5432

if %errorlevel% equ 0 (
    echo PostgreSQL muvaffaqiyatda ishga tushurildi!
    echo Port: 5432
) else (
    echo PostgreSQL ishlamadi
)

echo.
echo 5. Tender Intelligence Platform uchun tayyorlanish...
echo    - API Server: http://localhost:8002
echo    - Telegram Bot: @TIPtestt_bot
echo    - Real-Time Monitoring: Faol
echo.
pause
