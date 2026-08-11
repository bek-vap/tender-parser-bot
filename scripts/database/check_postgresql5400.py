import os
import subprocess

print("PostgreSQL 18 tekshirish - Port 5400")
print("=" * 50)

pg_path = r"C:\Program Files\PostgreSQL\18\bin"

if os.path.exists(pg_path):
    print(f"PostgreSQL 18 o'rnatilgan: {pg_path}")
    
    # PostgreSQL holatini tekshirish - Port 5400
    check_cmd = f'"{pg_path}\\pg_isready" -h localhost -p 5400'
    print(f"Tekshirilayotgan: {check_cmd}")
    result = subprocess.run(check_cmd, shell=True, capture_output=True, text=True)
    print(f"Natija: {result.stdout.strip()}")
    
    if result.returncode == 0:
        print("PostgreSQL ishlatilgan bo'lishi - Port 5400!")
        print("\nTender Intelligence Platform uchun tayyorlanish:")
        print("1. API Server: cd C:\\Users\\asadi\\Desktop\\tender\\TENDER-INTELLIGENCE-PLATFORM\\backend_py")
        print("2. set PYTHONPATH=C:\\Users\\asadi\\Desktop\\tender\\TENDER-INTELLIGENCE-PLATFORM\\backend_py")
        print("3. py -m uvicorn app.main:app --host 0.0.0.0 --port 8000")
        print("\nTelegram Bot: python test_telegram_fixed.py")
        print("API Documentation: http://localhost:8000/docs")
    else:
        print("PostgreSQL ishlamayapti - Port 5400")
        print("PostgreSQL ishga tushurish...")
        start_cmd = f'"{pg_path}\\pg_ctl" start -D "C:\\Program Files\\PostgreSQL\\18\\data"'
        print(f"Ishga tushurilayotgan: {start_cmd}")
        result = subprocess.run(start_cmd, shell=True, capture_output=True, text=True)
        print(f"Natija: {result.stdout.strip()}")
else:
    print("PostgreSQL 18 o'rnatilmadi")

input("\nChiqish uchun Enter tugmasang...")
