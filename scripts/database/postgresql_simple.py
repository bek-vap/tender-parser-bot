import os
import subprocess
import sys

print("PostgreSQL ma'lumotini tuzatish")
print("=" * 50)

def run_admin_command(command, description):
    """Run command with administrator privileges"""
    print(f"\n{description}...")
    print(f"Ishga tushurilayotgan: {command}")
    
    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True)
        if result.returncode == 0:
            print(f"Natija: {result.stdout.strip()}")
            return True
        else:
            print(f"Xato: {result.stderr.strip()}")
            return False
    except Exception as e:
        print(f"Xato: {e}")
        return False

def setup_postgresql():
    """Setup PostgreSQL database"""
    
    # 1. PostgreSQL o'rnatish xizmatlarini tekshirish
    paths = [
        r"C:\Program Files\PostgreSQL\16\bin",
        r"C:\Program Files\PostgreSQL\15\bin",
        r"C:\Program Files\PostgreSQL\14\bin"
    ]
    
    pg_path = None
    for i, path in enumerate(paths, 1):
        if os.path.exists(path):
            print(f"   {i}. Path: Mavjud")
            pg_path = path
            break
        else:
            print(f"   {i}. Path: Topilmadi")
    
    if not pg_path:
        print("   Hech qanday PostgreSQL o'rnatilmadi!")
        return False
    
    # 2. PostgreSQL ma'lumotini boshlash
    data_dir = r"C:\Program Files\PostgreSQL\16\data"
    if not os.path.exists(data_dir):
        print("   Data papka yaratilmoqda...")
        try:
            os.makedirs(data_dir, exist_ok=True)
            print(f"   Data papka yaratildi: {data_dir}")
        except Exception as e:
            print(f"   Xato: {e}")
            return False
    
    # Initialize database
    init_cmd = f'"{pg_path}\\pg_ctl" init -D "{data_dir}"'
    if not run_admin_command(init_cmd, "PostgreSQL ma'lumotini boshlash"):
        return False
    
    # 3. PostgreSQL ishga tushurish
    start_cmd = f'"{pg_path}\\pg_ctl" start -D "{data_dir}"'
    if not run_admin_command(start_cmd, "PostgreSQL ishga tushurish"):
        return False
    
    # 4. PostgreSQL holatini tekshirish
    check_cmd = f'"{pg_path}\\pg_isready" -h localhost -p 5432'
    if not run_admin_command(check_cmd, "PostgreSQL holatini tekshirish"):
        return False
    
    return True

def main():
    print("Tender Intelligence Platform - PostgreSQL ma'lumotini")
    print("O'zbekistoncha ishlash:")
    print("1. PostgreSQL o'rnatish xizmatlarini tekshirish")
    print("2. PostgreSQL ma'lumotini boshlash")
    print("3. PostgreSQL ishga tushurish")
    print("4. PostgreSQL holatini tekshirish")
    print("5. Tender Intelligence Platform uchun tayyorlanish")
    print("\n" + "=" * 50)
    
    if setup_postgresql():
        print("\n" + "=" * 50)
        print("QADAMLAR:")
        print("1. PostgreSQL muvaffaqiyatli ishlatilgan bo'lishi!")
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
        print("\n❌ PostgreSQL ma'lumotini tuzatish muvaffaq bo'lmadi!")
        print("Iltimos: Administrator sifatida PostgreSQL ni o'rnatish kerak")
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
