import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.db.session import SessionLocal
from app.models.tender import Tender

db = SessionLocal()
try:
    for source in ["UZEX", "XARID_UZEX", "TENDER_MC", "E_AUKSION"]:
        tenders = db.query(Tender).filter(Tender.source == source).order_by(Tender.created_at.desc()).limit(3).all()
        print("=" * 80)
        print(f"Source: {source} (Total in DB: {db.query(Tender).filter(Tender.source == source).count()})")
        for t in tenders:
            print(f"  ID: {t.id} | External ID: {t.external_id}")
            print(f"  Title: {t.title}")
            print(f"  URL: {t.url}")
            print(f"  Created At: {t.created_at}")
            print("-" * 50)
finally:
    db.close()
