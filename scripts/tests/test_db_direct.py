import sys
import os

# Add backend directory to Python path
backend_path = r"C:\Users\asadi\Desktop\tender\TENDER-INTELLIGENCE-PLATFORM\backend_py"
if backend_path not in sys.path:
    sys.path.insert(0, backend_path)

print("Database Connection Test - Tender Intelligence Platform")
print("=" * 50)

try:
    from app.core.config import settings
    from sqlalchemy import create_engine, text
    
    print("Configuration:")
    print(f"  Database URL: {settings.DATABASE_URL[:50]}...")
    print(f"  Redis URL: {settings.REDIS_URL}")
    print(f"  Telegram Bot: {'Configured' if settings.TELEGRAM_BOT_TOKEN else 'Not configured'}")
    
    print("\nTesting database connection...")
    
    # Test database connection
    engine = create_engine(settings.DATABASE_URL, connect_args={"connect_timeout": 10})
    
    with engine.connect() as connection:
        result = connection.execute(text("SELECT 1 as test"))
        print("Database connection: SUCCESS")
        print("PostgreSQL is ready for Tender Intelligence Platform!")
        
        # Test if tables exist
        try:
            tables_result = connection.execute(text("""
                SELECT table_name FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_name IN ('tenders', 'keywords', 'winners', 'company_profiles')
            """))
            
            tables = [row[0] for row in tables_result]
            print(f"Tables found: {tables}")
            
            # Test keyword count
            if 'keywords' in tables:
                count_result = connection.execute(text("SELECT COUNT(*) FROM keywords"))
                keyword_count = count_result.scalar()
                print(f"Keywords in database: {keyword_count}")
            
        except Exception as e:
            print(f"Table check failed: {e}")
    
    print("\n" + "=" * 50)
    print("Database test completed successfully!")
    print("Your Tender Intelligence Platform database is ready!")
    
except ImportError as e:
    print(f"Import error: {e}")
    print("Make sure you're in the correct directory and all dependencies are installed")
except Exception as e:
    print(f"Database connection failed: {e}")
    print("\nTroubleshooting:")
    print("1. Check if PostgreSQL is running")
    print("2. Verify database credentials in .env file")
    print("3. Ensure database 'tender' exists")

input("\nPress Enter to exit...")
