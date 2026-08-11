from app.db.session import SessionLocal
from app.models.tender import Keyword

def check_keywords() -> None:
    db = SessionLocal()
    try:
        keywords = db.query(Keyword).all()
        print(f"Total keywords in database: {len(keywords)}")
        for kw in keywords:
            print(f"  - {kw.phrase} (active: {kw.is_active})")
    finally:
        db.close()

if __name__ == "__main__":
    check_keywords()
