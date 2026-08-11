from app.db.session import SessionLocal
from app.models.tender import Tender

def fix_urls():
    db = SessionLocal()
    try:
        tenders = db.query(Tender).filter(
            Tender.source.in_(["UZEX", "UZEX_ETENDER"]),
            Tender.url == "https://etender.uzex.uz/"
        ).all()
        
        print(f"Found {len(tenders)} tenders with incorrect URLs.")
        
        updated = 0
        for t in tenders:
            if t.external_id:
                t.url = f"https://etender.uzex.uz/lot/{t.external_id}"
                updated += 1
        
        db.commit()
        print(f"Successfully updated {updated} URLs.")
    except Exception as e:
        print(f"Error: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    fix_urls()
