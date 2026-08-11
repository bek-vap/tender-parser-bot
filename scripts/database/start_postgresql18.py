import os
import subprocess
import time

print("PostgreSQL 18 ishga tushurish")
print("=" * 50)

pg_path = r"C:\Program Files\PostgreSQL\18\bin"
data_dir = r"C:\Program Files\PostgreSQL\18\data"

print(f"PostgreSQL 18: {pg_path}")
print(f"Data directory: {data_dir}")

# PostgreSQL ishga tushurish
start_cmd = f'"{pg_path}\\pg_ctl" start -D "{data_dir}"'
print(f"Ishga tushurilayotgan: {start_cmd}")

result = subprocess.run(start_cmd, shell=True, capture_output=True, text=True)
print(f"Natija: {result.stdout.strip()}")

if result.returncode == 0:
    print("PostgreSQL ishga tushurildi!")
    
    # 5 soniya kutish
    print("5 soniya kutish...")
    time.sleep(5)
    
    # PostgreSQL holatini tekshirish
    check_cmd = f'"{pg_path}\\pg_isready" -h localhost -p 5432'
    print(f"Tekshirilayotgan: {check_cmd}")
    result = subprocess.run(check_cmd, shell=True, capture_output=True, text=True)
    print(f"Natija: {result.stdout.strip()}")
    
    if result.returncode == 0:
        print("PostgreSQL ishlatilgan bo'lishi!")
        print("\nTender Intelligence Platform uchun tayyorlanish:")
        print("1. API Server: cd C:\\Users\\asadi\\Desktop\\tender\\TENDER-INTELLIGENCE-PLATFORM\\backend_py")
        print("2. set PYTHONPATH=C:\\Users\\asadi\\Desktop\\tender\\TENDER-INTELLIGENCE-PLATFORM\\backend_py")
        print("3. py -m uvicorn app.main:app --host 0.0.0.0 --port 8000")
        print("\nTelegram Bot: python test_telegram_fixed.py")
        print("API Documentation: http://localhost:8000/docs")
    else:
        print("PostgreSQL ishlamayapti")
else:
    print("PostgreSQL ishga tushurish muvaffaq bo'lmadi!")
    print(f"Xato: {result.stderr.strip()}")

input("\nChiqish uchun Enter tugmasang...")
