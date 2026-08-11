import sys
import os

# Add backend to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))) + "/backend_py")

from app.db.session import SessionLocal
from app.models.tender import Tender

if __name__ == "__main__":
    db = SessionLocal()
    try:
        tenders = db.query(Tender).filter(Tender.source.in_(["UZEX", "UZEX_ETENDER"])).limit(20).all()
        print(f"Total UZEX tenders: {db.query(Tender).filter(Tender.source.in_(['UZEX', 'UZEX_ETENDER'])).count()}")
        for t in tenders:
            print(f"ID: {t.id}, External ID: {t.external_id}, Title: {t.title[:50]}, URL: {t.url}")
    finally:
        db.close()
