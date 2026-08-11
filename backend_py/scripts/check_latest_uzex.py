from app.db.session import SessionLocal
from app.models.tender import Tender

def main():
    db = SessionLocal()
    try:
        total = db.query(Tender).count()
        print(f"TOTAL_TENDERS={total}")
        for src in ['UZEX', 'XARID_UZEX', 'TENDER_MC', 'E_AUKSION']:
            cnt = db.query(Tender).filter(Tender.source == src).count()
            print(f"COUNT_{src}={cnt}")
        
        # Print latest 5 tenders of any source
        tenders = db.query(Tender).order_by(Tender.created_at.desc()).limit(5).all()
        for t in tenders:
            print(f"Tender: id={t.id}, source={t.source}, external_id={t.external_id}, title={t.title[:50]}")
    finally:
        db.close()

if __name__ == "__main__":
    main()
