"""
Backfill organizer_inn from trade_list API for existing UZEX tenders
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.db.session import SessionLocal
from app.models.tender import Tender
from app.clients.uzex_etender_api import UzexEtenderApiClient

def run():
    db = SessionLocal()
    api = UzexEtenderApiClient()
    
    try:
        # Fetch current trade list (up to 100 items)
        items = api.trade_list(type_id=2, from_=1, to=100, system_id=0)
        print(f"Fetched {len(items)} items from API trade_list")
        
        # Build a map of external_id -> seller_tin
        tin_map = {}
        for it in items:
            if it.seller_tin:
                tin_map[str(it.id)] = str(it.seller_tin)
        
        print(f"Found {len(tin_map)} items with seller_tin")
        
        # Update tenders in DB
        updated = 0
        tenders = db.query(Tender).filter(
            Tender.source.in_(["UZEX", "UZEX_ETENDER"]),
            Tender.organizer_inn == None
        ).all()
        
        for t in tenders:
            if t.external_id in tin_map:
                t.organizer_inn = tin_map[t.external_id]
                updated += 1
                print(f"  Updated {t.external_id} -> INN: {tin_map[t.external_id]}")
        
        db.commit()
        print(f"Done. Updated {updated}/{len(tenders)} tenders")
    except Exception as e:
        print(f"Error: {e}")
        db.rollback()
    finally:
        api.close()
        db.close()

if __name__ == "__main__":
    run()
