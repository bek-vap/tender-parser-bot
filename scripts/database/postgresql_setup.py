import subprocess
import time
import os

print("PostgreSQL ma'lumotini tuzatish")
print("=" * 50)

# PostgreSQL o'rnatish uchun kerakli xizmatlari
postgresql_paths = [
    r"C:\Program Files\PostgreSQL\16\bin",
    r"C:\Program Files\PostgreSQL\15\bin",
    r"C:\Program Files\PostgreSQL\14\bin",
    r"C:\Program Files\PostgreSQL\13\bin",
    r"C:\Program Files\PostgreSQL\12\bin"
]

# PostgreSQL ma'lumotini keraklari
postgresql_services = [
    "postgresql-16",
    "postgresql-15", 
    "postgresql-14",
    "postgresql-13",
    "postgresql-12",
    "postgresql-x64-16",
    "postgresql-x64-15",
    "postgresql-x64-14",
    "postgresql-x64-13",
    "postgresql-x64-12"
]

# PostgreSQL xizmatlari
postgresql_commands = [
    "pg_isready -h localhost -p 5432",
    "pg_ctl init -D \"C:\\Program Files\\PostgreSQL\\16\\data\"",
    "pg_ctl start -D \"C:\\Program Files\\PostgreSQL\\16\\data\"",
    "pg_ctl status -D \"C:\\Program Files\\PostgreSQL\\16\\data\"",
    "pg_ctl stop -D \"C:\\Program Files\\PostgreSQL\\16\\data\""
]

# PostgreSQL xizmatlari tekshirish
def setup_postgresql():
    print("1. PostgreSQL o'rnatish xizmatlarini tekshirish...")
    
    for i, path in enumerate(postgresql_paths, 1):
        print(f"   {i}. Path: {path}")
        if os.path.exists(path):
            print(f"   Status: Mavjud")
            return path, True
        else:
            print(f"   Status: Topilmadi")
    
    print("   Hech qanday PostgreSQL o'rnatilmadi!")
    return None, False

def init_database():
    print("\n2. PostgreSQL ma'lumotini boshlash...")
    
    # Create data directory
    data_dir = "C:\\Program Files\\PostgreSQL\\16\\data"
    if not os.path.exists(data_dir):
        os.makedirs(data_dir, exist_ok=True)
        print(f"   Data papka yaratildi: {data_dir}")
    
    # Initialize database
    init_cmd = 'pg_ctl init -D "C:\\Program Files\\PostgreSQL\\16\\data"'
    print(f"   Ishga tushurilayotgan: {init_cmd}")
    
    result = subprocess.run(init_cmd, shell=True, capture_output=True, text=True)
    if result.returncode == 0:
        print("   Natija: Ma'lumot boshlandi!")
        return True
    else:
        print(f"   Xato: {result.stderr}")
        return False

def start_postgresql():
    print("\n3. PostgreSQL ishga tushurish...")
    
    start_cmd = 'pg_ctl start -D "C:\\Program Files\\PostgreSQL\\16\\data"'
    print(f"   Ishga tushurilayotgan: {start_cmd}")
    
    result = subprocess.run(start_cmd, shell=True, capture_output=True, text=True)
    if result.returncode == 0:
        print("   Natija: PostgreSQL ishga tushurildi!")
        return True
    else:
        print(f"   Xato: {result.stderr}")
        return False

def check_postgresql_status():
    print("\n4. PostgreSQL holatini tekshirish...")
    
    check_cmd = 'pg_isready -h localhost -p 5432'
    print(f"   Tekshirilayotgan: {check_cmd}")
    
    result = subprocess.run(check_cmd, shell=True, capture_output=True, text=True)
    if result.returncode == 0:
        print("   Natija: PostgreSQL ishlatilgan bo'lishi!")
        return True
    else:
        print(f"   Xato: {result.stderr}")
        return False

def main():
    print("Tender Intelligence Platform - PostgreSQL ma'lumotini")
    print("O'zbekistoncha ishlash:")
    print("1. PostgreSQL o'rnatish xizmatlarini tekshirish")
    print("2. PostgreSQL ma'lumotini boshlash")
    print("3. PostgreSQL ishga tushurish")
    print("4. PostgreSQL holatini tekshirish")
    print("5. Tender Intelligence Platform uchun tayyorlanish")
    print("\n" + "=" * 50)
    
    # 1-qadam: PostgreSQL o'rnatish xizmatlarini tekshirish
    path, found = setup_postgresql()
    if not found:
        print("   Xato: PostgreSQL o'rnatilmadi!")
        print("   Iltimos: PostgreSQL ni o'rnatish kerakli xizmatlarini tekshiring")
        return False
    
    # 2-qadam: PostgreSQL ma'lumotini boshlash
    if not init_database():
        print("   Xato: Ma'lumot boshlash muvaffaq bo'lmadi!")
        return False
    
    # 3-qadam: PostgreSQL ishga tushurish
    if not start_postgresql():
        print("   Xato: PostgreSQL ishga tushurish muvaffaq bo'lmadi!")
        return False
    
    # 4-qadam: PostgreSQL holatini tekshirish
    print("   5 soniya kutish...")
    time.sleep(5)
    
    if check_postgresql_status():
        print("   ✅ PostgreSQL muvaffaqiyatli ishga tushurildi!")
        print("   ✅ Port: 5432")
        print("   ✅ Data: C:\\Program Files\\PostgreSQL\\16\\data")
        print("   ✅ Tender Intelligence Platform uchun tayyor!")
        
        print("\n" + "=" * 50)
        print("QADAMLAR:")
        print("1. API Server: cd C:\\Users\\asadi\\Desktop\\tender\\TENDER-INTELLIGENCE-PLATFORM\\backend_py")
        print("   set PYTHONPATH=C:\\Users\\asadi\\Desktop\\tender\\TENDER-INTELLIGENCE-PLATFORM\\backend_py")
        print("   py -m uvicorn app.main:app --host 0.0.0.0 --port 8000")
        print("\n2. Telegram Bot: python test_telegram_fixed.py")
        print("3. Celery Worker: py -m celery -A app.workers.celery_app worker --loglevel=info")
        print("4. Celery Beat: py -m celery -A app.workers.celery_app beat --loglevel=info")
        print("\n4. API Documentation: http://localhost:8000/docs")
        print("\n🎉 Tender Intelligence Platform to'liq ishga tayyor!")
        
        return True
    else:
        print("   ❌ PostgreSQL ishlamadi!")
        return False

if __name__ == "__main__":
    main()
    
    input("\nChiqish uchun Enter tugmasang...")
