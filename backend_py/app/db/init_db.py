from app.db.base import Base
from app.db.session import engine

# Ensure models are imported so they register on Base.metadata
from app import models  # noqa: F401


def init_db() -> None:
    Base.metadata.create_all(bind=engine)
    
    from app.db.session import SessionLocal
    from app.models.tender import Keyword
    
    db = SessionLocal()
    try:
        count = db.query(Keyword).count()
        print("Seeding initial keywords into database...")
        try:
            from scripts.seed_keywords import INITIAL_KEYWORDS
        except ImportError:
            INITIAL_KEYWORDS = [
                "теплица", "issiqxona", "ferma", "chorva", "parnik", "angar", "ombor", "sklad", 
                "klaster", "zavod", "sex", "qurilish", "stroyka", "rekonstruksiya", "modernizatsiya",
                "remont", "tender", "konkurs", "закупка", "поставка", "строительство", "монтаж"
            ]
            
        added = 0
        seen_phrases = set()
        for phrase in INITIAL_KEYWORDS:
            phrase_clean = phrase.strip().lower()
            if not phrase_clean or phrase_clean in seen_phrases:
                continue
            seen_phrases.add(phrase_clean)
            
            # Check if this keyword already exists in the database
            exists = db.query(Keyword).filter(Keyword.phrase == phrase_clean).first()
            if not exists:
                db.add(Keyword(phrase=phrase_clean))
                added += 1
        
        if added > 0:
            db.commit()
            print(f"Successfully auto-seeded {added} new initial keywords.")
        else:
            print("🌱 No new keywords to seed.")
    except Exception as e:
        print(f"Warning: Auto-seeding keywords failed: {e}")
    finally:
        db.close()
