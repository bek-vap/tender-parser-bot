import os
import subprocess

print("PostgreSQL 18 tekshirish")
print("=" * 50)

# PostgreSQL 18 o'rnatish xizmatlarini tekshirish
pg_path = r"C:\Program Files\PostgreSQL\18\bin"

if os.path.exists(pg_path):
    print(f"PostgreSQL 18 o'rnatilgan: {pg_path}")
    
    # PostgreSQL holatini tekshirish
    check_cmd = f'"{pg_path}\\pg_isready" -h localhost -p 5432'
    print(f"Tekshirilayotgan: {check_cmd}")
    result = subprocess.run(check_cmd, shell=True, capture_output=True, text=True)
    print(f"Natija: {result.stdout.strip()}")
    
    if result.returncode == 0:
        print("PostgreSQL ishlatilgan bo'lishi!")
    else:
        print("PostgreSQL ishlamayapti")
        print("PostgreSQL ishga tushurish...")
        start_cmd = f'"{pg_path}\\pg_ctl" start -D "C:\\Program Files\\PostgreSQL\\18\\data"'
        print(f"Ishga tushurilayotgan: {start_cmd}")
        result = subprocess.run(start_cmd, shell=True, capture_output=True, text=True)
        print(f"Natija: {result.stdout.strip()}")
else:
    print("PostgreSQL 18 o'rnatilmadi")

input("\nChiqish uchun Enter tugmasang...")
