import subprocess
import time

print("PostgreSQL ma'lumotini tuzatish")
print("=" * 50)

# PostgreSQL xizmatlarini tekshirish
print("1. PostgreSQL xizmatlarini tekshiramiz...")
commands = [
    'netstat -an | findstr ":5432"',
    'tasklist | findstr postgres',
    'sc query postgres'
]

for cmd in commands:
    print(f"   Ishga tushurilayotgan buyruq: {cmd}")
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        if result.returncode == 0:
            print(f"   Natija: {result.stdout.strip()}")
        else:
            print(f"   Xato: {result.stderr.strip()}")
    except Exception as e:
        print(f"   Xato: {e}")

print("\n2. PostgreSQL xizmatini tekshirish...")
# PostgreSQL xizmatini ishga tushurish
start_commands = [
    'net start postgresql-18',
    'pg_ctl start -D "C:\\Program Files\\PostgreSQL\\18\\data"',
    'sc start postgresql-18'
]

for cmd in start_commands:
    print(f"   Ishga tushurilayotgan buyruq: {cmd}")
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        if result.returncode == 0:
            print(f"   Natija: {result.stdout.strip()}")
            print("   PostgreSQL muvaffaqiyat boshlandi!")
            break
        else:
            print(f"   Xato: {result.stderr.strip()}")
    except Exception as e:
        print(f"   Xato: {e}")

print("\n3. Ma'lumot holatini tekshirish...")
# Ma'lumot holatini tekshirish
check_commands = [
    'pg_isready -h localhost -p 5432',
    'C:\\Program Files\\PostgreSQL\\18\\bin\\pg_isready -h localhost -p 5432'
]

for cmd in check_commands:
    print(f"   Tekshirilayotgan buyruq: {cmd}")
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        if result.returncode == 0:
            print(f"   Natija: {result.stdout.strip()}")
            print("   PostgreSQL ma'lumot holatini to'g'ri!")
            break
        else:
            print(f"   Xato: {result.stderr.strip()}")
    except Exception as e:
        print(f"   Xato: {e}")

print("\n4. Ma'lumot ma'lumotini to'xtatish...")
# Ma'lumot ma'lumotini to'xtatish
stop_commands = [
    'net stop postgresql-18',
    'pg_ctl stop -D "C:\\Program Files\\PostgreSQL\\18\\data"',
    'sc stop postgresql-18'
]

for cmd in stop_commands:
    print(f"   To'xtatilayotgan buyruq: {cmd}")
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        if result.returncode == 0:
            print(f"   Natija: {result.stdout.strip()}")
            print("   PostgreSQL to'xtatildi!")
            break
        else:
            print(f"   Xato: {result.stderr.strip()}")
    except Exception as e:
        print(f"   Xato: {e}")

print("\n" + "=" * 50)
print("PostgreSQL ma'lumotini tuzatish yakunlandi!")
print("\nKeyingi qadamlar:")
print("1. PostgreSQL xizmatlari tekshirildi")
print("2. PostgreSQL ishga tushurildi")
print("3. PostgreSQL ma'lumot holati tekshirildi")
print("4. PostgreSQL to'xtatildi")
print("\nAgar muammolar bo'lsa:")
print("- PostgreSQL o'rnatilgan bo'lishi mumkin")
print("- PostgreSQL 5432 porti ishlatilgan bo'lishi kerak")
print("- Tender Intelligence Platform ma'lumotini to'g'ri uchun PostgreSQL kerak")

input("\nChiqish uchun Enter tugmasang...")
