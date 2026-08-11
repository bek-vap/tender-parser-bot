import psycopg2
from psycopg2 import OperationalError

print("PostgreSQL ma'lumotini tekshirish - Port 5400")
print("=" * 50)

try:
    # PostgreSQL ma'lumotini bilan bog'lanish
    connection = psycopg2.connect(
        host="localhost",
        port=5400,
        database="tender",
        user="postgres",
        password="Jafarbek123000566j"
    )
    
    print("PostgreSQL muvaffaqiyat bilan bog'landi!")
    print("Host: localhost")
    print("Port: 5400")
    print("Database: tender")
    print("User: postgres")
    
    # Cursor yaratish
    cursor = connection.cursor()
    
    # Ma'lumotni tekshirish
    cursor.execute("SELECT version();")
    version = cursor.fetchone()
    print(f"\nPostgreSQL versiyasi: {version[0]}")
    
    # Ma'lumotlarni tekshirish
    cursor.execute("SELECT datname FROM pg_database WHERE datname = 'tender';")
    db_exists = cursor.fetchone()
    
    if db_exists:
        print(f"Tender ma'lumoti mavjud: {db_exists[0]}")
    else:
        print("Tender ma'lumoti topilmadi")
    
    # Bog'lanishni yopish
    cursor.close()
    connection.close()
    
    print("\nPostgreSQL ma'lumotini tekshirish muvaffaqiyatli!")
    print("\nTender Intelligence Platform uchun tayyorlanish:")
    print("1. API Server: cd C:\\Users\\asadi\\Desktop\\tender\\TENDER-INTELLIGENCE-PLATFORM\\backend_py")
    print("2. set PYTHONPATH=C:\\Users\\asadi\\Desktop\\tender\\TENDER-INTELLIGENCE-PLATFORM\\backend_py")
    print("3. py -m uvicorn app.main:app --host 0.0.0.0 --port 8000")
    print("\nTelegram Bot: python test_telegram_fixed.py")
    print("API Documentation: http://localhost:8000/docs")
    
except OperationalError as e:
    print(f"PostgreSQL bog'lanish xatoligi: {e}")
    print("\nIltimos:")
    print("1. PostgreSQL ishlatilgan bo'lishini tekshiring")
    print("2. Port 5400 to'g'ri ekanligini tekshiring")
    print("3. 'tender' ma'lumoti mavjudligini tekshiring")

input("\nChiqish uchun Enter tugmasang...")
