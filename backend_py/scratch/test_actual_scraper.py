import asyncio
import sys
import os
import json

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.scrapers.uzex_lot_scraper import UzexLotScraper, ScraperOptions

async def test_scraper():
    scraper = UzexLotScraper(opts=ScraperOptions(headless=True))
    lot_id = "484088"
    print(f"Testing real UzexLotScraper with lot {lot_id}...")
    
    data = await scraper.scrape_lot_details(lot_id)
    
    print("\nScraped Data:")
    print(json.dumps(data, indent=2, ensure_ascii=False))
    
    if data.get('organizer_inn') or data.get('phone') or data.get('status'):
        print("\n✅ SUCCESS: Data extracted correctly!")
    else:
        print("\n❌ FAILURE: Missing expected fields.")

if __name__ == "__main__":
    asyncio.run(test_scraper())
