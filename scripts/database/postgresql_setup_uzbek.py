import os
import subprocess
import time

print("PostgreSQL ma'lumotini tuzatish")
print("=" * 50)

# PostgreSQL o'rnatish uchun keraklari
postgresql_paths = [
    r"C:\Program Files\PostgreSQL\16\bin",
    r"C:\Program Files\PostgreSQL\15\bin",
    r"C:\Program Files\PostgreSQL\14\bin",
    r"C:\Program Files\PostgreSQL\13\bin",
    r"C:\Program Files\PostgreSQL\12\bin"
]

postgresql_services = [
    "postgresql-16",
    "postgresql-15", 
    "postgresql-14",
    "postgresql-13",
    "postgresql-12"
]

# Xizmatlarni tekshirish
def check_paths():
    print("1. PostgreSQL o'rnatish xizmatlarini tekshirish...")
    for i, path in enumerate(postgresql_paths, 1):
        if os.path.exists(path):
            print(f"   {i}. Path: Mavjud")
        else:
            print(f"   {i}. Path: Topilmadi")

def check_services():
    print("\n2. PostgreSQL xizmatlari tekshirish...")
    for i, service in enumerate(postgresql_services, 1):
        try:
            result = subprocess.run(["sc", "query", service], capture_output=True, text=True)
            status = "Ishga tushurilgan" if result.returncode == 0 else "To'xtatilgan"
            print(f"   {i}. Service: {status}")
        except:
            print(f"   {i}. Service: Xato")

def init_database():
    print("\n3. PostgreSQL ma'lumotini boshlash...")
    
    # Create data directory
    data_dir = r"C:\Program Files\PostgreSQL\16\data"
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
    print("\n4. PostgreSQL ishga tushurish...")
    
    start_cmd = 'pg_ctl start -D "C:\\Program Files\\PostgreSQL\\16\\data"'
    print(f"   Ishga tushurilayotgan: {start_cmd}")
    
    result = subprocess.run(start_cmd, shell=True, capture_output=True, text=True)
    if result.returncode == 0:
        print("   Natija: PostgreSQL ishlatilgan bo'lishi!")
        return True
    else:
        print(f"   Xato: {result.stderr}")
        return False

def check_status():
    print("\n5. PostgreSQL holatini tekshirish...")
    
    check_cmd = 'pg_isready -h localhost -p 5432'
    print(f"   Tekshirilayotgan: {check_cmd}")
    
    result = subprocess.run(check_cmd, shell=True, capture_output=True, text=True)
    if result.returncode == 0:
        print("   Natija: PostgreSQL ma'lumot holatini to'g'ri!")
        print("   Port: 5432")
        return True
    else:
        print(f"   Xato: {result.stderr}")
        return False

def stop_postgresql():
    print("\n6. PostgreSQL to'xtatish...")
    
    stop_cmd = 'pg_ctl stop -D "C:\\Program Files\\PostgreSQL\\16\\data"'
    print(f"   To'xtatilayotgan: {stop_cmd}")
    
    result = subprocess.run(stop_cmd, shell=True, capture_output=True, text=True)
    if result.returncode == 0:
        print("   Natija: PostgreSQL to'xtatildi!")
        return True
    else:
        print(f"   Xato: {result.stderr}")
        return False

def main():
    print("Tender Intelligence Platform - PostgreSQL ma'lumotini tuzatish")
    print("O'zbekistoncha ishlash:")
    print("1. PostgreSQL o'rnatish xizmatlarini tekshirish")
    print("2. PostgreSQL ma'lumotini boshlash")
    print("3. PostgreSQL ishga tushurish")
    print("4. PostgreSQL holatini tekshirish")
    print("5. Tender Intelligence Platform uchun tayyorlanish")
    print("\n" + "=" * 50)
    
    # 1-qadam: PostgreSQL o'rnatish xizmatlarini tekshirish
    check_paths()
    
    # 2-qadam: PostgreSQL xizmatlari tekshirish
    check_services()
    
    # 3-qadam: PostgreSQL ma'lumotini boshlash
    if init_database():
        # 4-qadam: PostgreSQL ishga tushurish
        if start_postgresql():
            # 5-qadam: PostgreSQL holatini tekshirish
            if check_status():
                print("\n" + "=" * 50)
                print("QADAMLAR:")
                print("1. API Server: cd C:\\Users\\asadi\\Desktop\\tender\\TENDER-INTELLIGENCE-PLATFORM\\backend_py")
                print("   set PYTHONPATH=C:\\Users\\asadi\\Desktop\\tender\\TENDER-INTELLIGENCE-PLATFORM\\backend_py")
                print("   py -m uvicorn app.main:app --host 0.0.0.0 --port 8000")
                print("\n2. Telegram Bot: python test_telegram_fixed.py")
                print("3. Celery Worker: py -m celery -A app.workers.celery_app worker --loglevel=info")
                print("4. Celery Beat: py -m celery -A app.workers.celery_app beat --loglevel=info")
                print("5. API Documentation: http://localhost:8000/docs")
                print("\n🎉 Tender Intelligence Platform to'liq ishga tayyor!")
                print("=" * 50)
                return True
            else:
                print("\n❌ PostgreSQL ishlamadi!")
                return False
    else:
        print("\n❌ PostgreSQL ma'lumotini boshlash muvaffaq bo'lmadi!")
        return False

if __name__ == "__main__":
    main()
    
    input("\nChiqish uchun Enter tugmasang...")
