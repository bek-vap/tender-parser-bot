import os
import subprocess

print("PostgreSQL tekshirish")
print("=" * 50)

# PostgreSQL o'rnatish xizmatlarini tekshirish
paths = [
    r"C:\Program Files\PostgreSQL\16\bin",
    r"C:\Program Files\PostgreSQL\15\bin",
    r"C:\Program Files\PostgreSQL\14\bin"
]

pg_path = None
for i, path in enumerate(paths, 1):
    if os.path.exists(path):
        print(f"{i}. Path: Mavjud - {path}")
        pg_path = path
        break
    else:
        print(f"{i}. Path: Topilmadi")

if pg_path:
    print(f"\nPostgreSQL o'rnatilgan: {pg_path}")
    
    # PostgreSQL holatini tekshirish
    check_cmd = f'"{pg_path}\\pg_isready" -h localhost -p 5432'
    print(f"Tekshirilayotgan: {check_cmd}")
    result = subprocess.run(check_cmd, shell=True, capture_output=True, text=True)
    print(f"Natija: {result.stdout.strip()}")
    
    if result.returncode == 0:
        print("PostgreSQL ishlatilgan bo'lishi!")
    else:
        print("PostgreSQL ishlamayapti")
else:
    print("PostgreSQL o'rnatilmadi")

input("\nChiqish uchun Enter tugmasang...")
