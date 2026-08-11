import sys
import os
from sqlalchemy import create_engine, text

# Add the parent directory to sys.path to allow importing from 'app'
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.config import settings
from app.db.base import Base
# Import all models to ensure they are registered with Base.metadata
import app.models.tender
import app.models.log
import app.models.winner
import app.models.telegram_channel
import app.models.admin

def fix_db():
    print(f"Connecting to database: {settings.DATABASE_URL}")
    engine = create_engine(settings.DATABASE_URL)
    
    print("Creating all missing tables...")
    Base.metadata.create_all(engine)
    print("Tables check/creation completed.")

    with engine.connect() as conn:
        print("Checking parser_logs table for missing columns...")
        columns_to_check = [
            ("task_name", "VARCHAR"),
            ("source", "VARCHAR"),
            ("status", "VARCHAR"),
            ("message", "TEXT"),
            ("details", "TEXT"),
            ("started_at", "TIMESTAMP"),
            ("completed_at", "TIMESTAMP"),
            ("duration_seconds", "INTEGER"),
            ("items_processed", "INTEGER"),
            ("items_found", "INTEGER"),
            ("items_skipped", "INTEGER"),
            ("captcha_detected", "BOOLEAN DEFAULT FALSE"),
            ("error_traceback", "TEXT")
        ]
        
        for col_name, col_type in columns_to_check:
            try:
                result = conn.execute(text(f"SELECT column_name FROM information_schema.columns WHERE table_name='parser_logs' AND column_name='{col_name}'"))
                if not result.fetchone():
                    print(f"Column '{col_name}' missing. Adding it...")
                    conn.execute(text(f"ALTER TABLE parser_logs ADD COLUMN {col_name} {col_type}"))
                    conn.commit()
                    print(f"Column '{col_name}' added successfully.")
                else:
                    print(f"Column '{col_name}' already exists.")
            except Exception as e:
                print(f"Error checking/adding column {col_name}: {e}")

        print("Checking tenders table for new columns...")
        columns_to_add = [
            ("metadata_json", "JSONB"),
            ("organizer_phone", "VARCHAR"),
            ("organizer_email", "VARCHAR")
        ]
        for col_name, col_type in columns_to_add:
            try:
                result = conn.execute(text(f"SELECT column_name FROM information_schema.columns WHERE table_name='tenders' AND column_name='{col_name}'"))
                if not result.fetchone():
                    print(f"Column '{col_name}' missing in tenders. Adding it...")
                    conn.execute(text(f"ALTER TABLE tenders ADD COLUMN {col_name} {col_type}"))
                    conn.commit()
                    print(f"Column '{col_name}' added successfully.")
                else:
                    print(f"Column '{col_name}' already exists in tenders.")
            except Exception as e:
                print(f"Error checking/adding column {col_name} in tenders: {e}")

        print("Checking keywords table for new columns...")
        try:
            result = conn.execute(text("SELECT column_name FROM information_schema.columns WHERE table_name='keywords' AND column_name='is_blacklist'"))
            if not result.fetchone():
                print("Column 'is_blacklist' missing in keywords. Adding it...")
                conn.execute(text("ALTER TABLE keywords ADD COLUMN is_blacklist BOOLEAN DEFAULT FALSE"))
                conn.commit()
                print("Column 'is_blacklist' added successfully.")
            else:
                print("Column 'is_blacklist' already exists in keywords.")
        except Exception as e:
            print(f"Error checking/adding column is_blacklist in keywords: {e}")

if __name__ == "__main__":
    fix_db()
