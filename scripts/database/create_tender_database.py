import psycopg2
from psycopg2 import OperationalError

print("Tender ma'lumotini yaratish")
print("=" * 50)

try:
    # PostgreSQL ma'lumotini bilan bog'lanish (postgres database)
    connection = psycopg2.connect(
        host="localhost",
        port=5400,
        database="postgres",
        user="postgres",
        password="Jafarbek123000566j"
    )
    
    print("PostgreSQL muvaffaqiyat bilan bog'landi!")
    
    # Cursor yaratish
    cursor = connection.cursor()
    
    # Tender ma'lumotini yaratish
    cursor.execute("CREATE DATABASE tender;")
    print("Tender ma'lumoti yaratildi!")
    
    # Bog'lanishni yopish
    cursor.close()
    connection.close()
    
    print("\nTender ma'lumotini yaratish muvaffaqiyatli!")
    print("\nEndi Tender Intelligence Platform uchun tayyorlanish:")
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

input("\nChiqish uchun Enter tugmasang...")
