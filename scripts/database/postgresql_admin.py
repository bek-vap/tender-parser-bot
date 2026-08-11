import os
import subprocess
import sys

print("PostgreSQL ma'lumotini tuzatish - Administrator sifati")
print("=" * 50)

def run_as_admin():
    """Run PostgreSQL setup with administrator privileges"""
    
    print("1. PostgreSQL o'rnatish xizmatlarini tekshirish...")
    
    # PostgreSQL o'rnatish uchun kerakli xizmatlar
    postgresql_paths = [
        r"C:\Program Files\PostgreSQL\16\bin",
        r"C:\Program Files\PostgreSQL\15\bin",
        r"C:\Program Files\PostgreSQL\14\bin",
        r"C:\Program Files\PostgreSQL\13\bin"
    ]
    
    for i, path in enumerate(postgresql_paths, 1):
        if os.path.exists(path):
            print(f"   {i}. Path: Mavjud - {path}")
            return path
        else:
            print(f"   {i}. Path: Topilmadi")
    
    print("   Hech qanday PostgreSQL o'rnatilmadi!")
    return None

def create_database():
    """Create PostgreSQL database with administrator privileges"""
    
    print("\n2. PostgreSQL ma'lumotini boshlash...")
    
    # Create data directory
    data_dir = r"C:\Program Files\PostgreSQL\16\data"
    if not os.path.exists(data_dir):
        try:
            os.makedirs(data_dir, exist_ok=True)
            print(f"   Data papka yaratildi: {data_dir}")
        except Exception as e:
            print(f"   Xato: {e}")
            return False
    
    # Initialize database
    init_cmd = 'pg_ctl init -D "C:\\Program Files\\PostgreSQL\\16\\data"'
    print(f"   Ishga tushurilayotgan: {init_cmd}")
    
    try:
        result = subprocess.run(init_cmd, shell=True, capture_output=True, text=True)
        if result.returncode == 0:
            print("   Natija: Ma'lumot boshlandi!")
            return True
        else:
            print(f"   Xato: {result.stderr}")
            return False
    except Exception as e:
        print(f"   Xato: {e}")
        return False

def start_postgresql():
    """Start PostgreSQL service with administrator privileges"""
    
    print("\n3. PostgreSQL ishga tushurish...")
    
    start_cmd = 'pg_ctl start -D "C:\\Program Files\\PostgreSQL\\16\\data"'
    print(f"   Ishga tushurilayotgan: {start_cmd}")
    
    try:
        result = subprocess.run(start_cmd, shell=True, capture_output=True, text=True)
        if result.returncode == 0:
            print("   Natija: PostgreSQL ishlatilgan bo'lishi!")
            return True
        else:
            print(f"   Xato: {result.stderr}")
            return False
    except Exception as e:
        print(f"   Xato: {e}")
        return False

def check_status():
    """Check PostgreSQL status"""
    
    print("\n4. PostgreSQL holatini tekshirish...")
    
    check_cmd = 'pg_isready -h localhost -p 5432'
    print(f"   Tekshirilayotgan: {check_cmd}")
    
    try:
        result = subprocess.run(check_cmd, shell=True, capture_output=True, text=True)
        if result.returncode == 0:
            print("   Natija: PostgreSQL ma'lumot holatini to'g'ri!")
            print("   Port: 5432")
            return True
        else:
            print(f"   Xato: {result.stderr}")
            return False
    except Exception as e:
        print(f"   Xato: {e}")
        return False

def main():
    print("Tender Intelligence Platform - PostgreSQL ma'lumotini")
    print("O'zbekistoncha ishlash (Administrator sifati):")
    print("1. PostgreSQL o'rnatish xizmatlarini tekshirish")
    print("2. PostgreSQL ma'lumotini boshlash")
    print("3. PostgreSQL ishga tushurish")
    print("4. PostgreSQL holatini tekshirish")
    print("5. Tender Intelligence Platform uchun tayyorlanish")
    print("\n" + "=" * 50)
    
    # 1-qadam: PostgreSQL o'rnatish xizmatlarini tekshirish
    pg_path = run_as_admin()
    if not pg_path:
        print("   Xato: PostgreSQL o'rnatilmadi!")
        print("   Iltimos: PostgreSQL ni administrator sifatida o'rnatish kerak")
        return False
    
    # 2-qadam: PostgreSQL ma'lumotini boshlash
    if not create_database():
        print("   Xato: Ma'lumot boshlash muvaffaq bo'lmadi!")
        return False
    
    # 3-qadam: PostgreSQL ishga tushurish
    if not start_postgresql():
        print("   Xato: PostgreSQL ishga tushurish muvaffaq bo'lmadi!")
        return False
    
    # 4-qadam: PostgreSQL holatini tekshirish
    print("   5 soniya kutish...")
    import time
    time.sleep(5)
    
    if check_status():
        print("\n" + "=" * 50)
        print("QADAMLAR:")
        print("1. PostgreSQL muvaffaqiyatli ishga tushurildi!")
        print("2. Port: 5432")
        print("3. Data: C:\\Program Files\\PostgreSQL\\16\\data")
        print("\nTender Intelligence Platform uchun tayyorlanish:")
        print("   API Server: cd C:\\Users\\asadi\\Desktop\\tender\\TENDER-INTELLIGENCE-PLATFORM\\backend_py")
        print("   set PYTHONPATH=C:\\Users\\asadi\\Desktop\\tender\\TENDER-INTELLIGENCE-PLATFORM\\backend_py")
        print("   py -m uvicorn app.main:app --host 0.0.0.0 --port 8000")
        print("\nTelegram Bot: python test_telegram_fixed.py")
        print("API Documentation: http://localhost:8000/docs")
        print("\n🎉 Tender Intelligence Platform to'liq ishga tayyor!")
        print("=" * 50)
        return True
    else:
        print("\n❌ PostgreSQL ishlamadi!")
        return False

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n🛑 Foydalanuvchi to'xtatildi")
    except Exception as e:
        print(f"\n❌ Xato: {e}")
    finally:
        input("\nChiqish uchun Enter tugmasang...")
