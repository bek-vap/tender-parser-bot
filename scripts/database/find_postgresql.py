import os
import subprocess

print("PostgreSQL qidirish")
print("=" * 50)

# PostgreSQL o'rnatish xizmatlarini keng qidirish
paths = [
    r"C:\Program Files\PostgreSQL\16\bin",
    r"C:\Program Files\PostgreSQL\15\bin",
    r"C:\Program Files\PostgreSQL\14\bin",
    r"C:\Program Files\PostgreSQL\13\bin",
    r"C:\Program Files\PostgreSQL\12\bin",
    r"C:\Program Files\PostgreSQL\11\bin",
    r"C:\Program Files\PostgreSQL\10\bin",
    r"C:\Program Files (x86)\PostgreSQL\16\bin",
    r"C:\Program Files (x86)\PostgreSQL\15\bin",
    r"C:\Program Files (x86)\PostgreSQL\14\bin",
    r"C:\Program Files (x86)\PostgreSQL\13\bin",
    r"C:\Program Files (x86)\PostgreSQL\12\bin",
    r"C:\Program Files (x86)\PostgreSQL\11\bin",
    r"C:\Program Files (x86)\PostgreSQL\10\bin"
]

pg_path = None
for i, path in enumerate(paths, 1):
    if os.path.exists(path):
        print(f"{i}. Path: Mavjud - {path}")
        pg_path = path
        break
    else:
        print(f"{i}. Path: Topilmadi - {path}")

if not pg_path:
    print("\nPostgreSQL o'rnatilmadi!")
    print("Iltimos, PostgreSQL o'rnatilgan joyini tekshiring")
else:
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

input("\nChiqish uchun Enter tugmasang...")
