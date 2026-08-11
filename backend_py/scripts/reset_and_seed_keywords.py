from app.db.session import SessionLocal
from app.models.tender import Keyword
from app.core.config import settings

def reset_and_seed_keywords() -> None:
    print(f"Connecting to database: {settings.DATABASE_URL}")
    db = SessionLocal()
    try:
        # Удалить все существующие keywords
        db.query(Keyword).delete()
        db.commit()
        print("Cleared all existing keywords")
        
        # Добавить заново
        from scripts.seed_keywords import INITIAL_KEYWORDS
        
        added = 0
        for phrase in INITIAL_KEYWORDS:
            keyword = Keyword(phrase=phrase)
            db.add(keyword)
            added += 1

        db.commit()
        print(f"Added {added} new keywords")
    finally:
        db.close()

if __name__ == "__main__":
    reset_and_seed_keywords()
