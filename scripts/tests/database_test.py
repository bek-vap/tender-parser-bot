import sys
import os

# Add backend directory to Python path
backend_path = r"C:\Users\asadi\Desktop\tender\TENDER-INTELLIGENCE-PLATFORM\backend_py"
if backend_path not in sys.path:
    sys.path.insert(0, backend_path)

print("Database Connection Test")
print("=" * 40)

try:
    from app.core.config import settings
    
    print("Configuration:")
    print(f"  Database URL: {settings.DATABASE_URL[:50]}...")
    print(f"  Redis URL: {settings.REDIS_URL}")
    print(f"  Telegram Bot: {'Configured' if settings.TELEGRAM_BOT_TOKEN else 'Not configured'}")
    print(f"  Alert Chat ID: {'Configured' if settings.TELEGRAM_ALERT_CHAT_ID else 'Not configured'}")
    
    # Test database connection
    print("\nTesting database connection...")
    from sqlalchemy import create_engine, text
    
    engine = create_engine(settings.DATABASE_URL)
    
    with engine.connect() as connection:
        result = connection.execute(text("SELECT 1 as test"))
        print("Database connection: SUCCESS")
    
    print("\nTesting Redis connection...")
    import redis
    r = redis.from_url(settings.REDIS_URL)
    r.ping()
    print("Redis connection: SUCCESS")
    
    print("\n" + "=" * 40)
    print("All connections successful!")
    print("Your Tender Intelligence Platform is ready for real-time testing!")
    print("\nNext steps:")
    print("1. Start API server: uvicorn app.main:app --host 0.0.0.0 --port 8000")
    print("2. Test Telegram bot: python test_telegram_fixed.py") 
    print("3. Monitor for real-time alerts")
    
except Exception as e:
    print(f"Connection test failed: {e}")
    print("\nTroubleshooting:")
    print("1. Check if PostgreSQL is running on port 5400")
    print("2. Check if Redis is running on port 6379")
    print("3. Verify database credentials in .env file")

input("\nPress Enter to exit...")
