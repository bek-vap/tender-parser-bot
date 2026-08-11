import asyncio
import os
import sys

# Add the parent directory to sys.path so we can import 'app'
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.clients.uzex_etender_api import UzexEtenderApiClient
from app.db.session import SessionLocal
from app.models.tender import Tender

async def main():
    api = UzexEtenderApiClient()
    db = SessionLocal()
    try:
        # Check Type 1
        print("Fetching type_id=1 (Tender)...")
        items_1 = await api.trade_list(type_id=1, from_=1, to=50, system_id=0)
        print(f"Type 1 returned {len(items_1)} items")
        
        # Check Type 2
        print("Fetching type_id=2 (Selection)...")
        items_2 = await api.trade_list(type_id=2, from_=1, to=50, system_id=0)
        print(f"Type 2 returned {len(items_2)} items")
        
        # Let's see if any items in Type 1 or Type 2 are in the DB or duplicates
        for t_type, items in [("Type 1", items_1), ("Type 2", items_2)]:
            print(f"\nDuplicate check for {t_type}:")
            dups = 0
            new = 0
            for it in items[:10]:
                existing = db.query(Tender).filter(Tender.external_id == str(it.id)).first()
                if existing:
                    dups += 1
                else:
                    new += 1
                    print(f"  NEW -> ID: {it.id}, Title: {it.name[:50]}")
            print(f"  Summary of first 10 items: {new} NEW, {dups} Duplicates")
            
    except Exception as e:
        print(f"Error: {e}")
    finally:
        await api.close()
        db.close()

if __name__ == "__main__":
    asyncio.run(main())
