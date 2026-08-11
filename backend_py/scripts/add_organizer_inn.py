import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.db.session import SessionLocal
from sqlalchemy import text

def run():
    db = SessionLocal()
    
    columns_to_add = [
        ("organizer_name", "VARCHAR"),
        ("organizer_phone", "VARCHAR"),
        ("organizer_email", "VARCHAR"),
        ("organizer_inn", "VARCHAR"),
        ("metadata_json", "JSONB"),
    ]
    
    try:
        for col_name, col_type in columns_to_add:
            result = db.execute(text(f"""
                SELECT column_name FROM information_schema.columns 
                WHERE table_name='tenders' AND column_name='{col_name}'
            """))
            if result.fetchone():
                print(f"SKIP - {col_name} already exists")
            else:
                db.execute(text(f"ALTER TABLE tenders ADD COLUMN {col_name} {col_type}"))
                print(f"ADDED - {col_name} ({col_type})")
        
        # Add index on organizer_inn if not exists
        try:
            db.execute(text("CREATE INDEX IF NOT EXISTS ix_tenders_organizer_inn ON tenders (organizer_inn)"))
            print("INDEX - ix_tenders_organizer_inn created/exists")
        except Exception:
            pass
        
        db.commit()
        print("DONE - All columns verified")
    except Exception as e:
        print(f"ERROR: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    run()
