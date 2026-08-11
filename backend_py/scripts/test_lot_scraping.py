import asyncio
from app.services.lot_search_service import get_lot_search_service
import json

async def test_lot_scraping():
    service = get_lot_search_service()
    lot_id = "484088"
    print(f"Testing scraping for lot {lot_id}...")
    
    data = await service.get_detailed_lot_info(lot_id)
    print("Scraped Data:")
    print(json.dumps(data, indent=2, ensure_ascii=False))
    
    if data.get('languages') or data.get('phone'):
        print("SUCCESS: Data extracted correctly!")
    else:
        print("FAILURE: Missing expected fields.")

if __name__ == "__main__":
    asyncio.run(test_lot_scraping())
