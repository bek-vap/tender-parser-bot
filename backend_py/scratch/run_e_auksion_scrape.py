import sys, os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import asyncio
from app.scrapers.e_auksion import EAuksionScraper, ScraperOptions

async def run():
    scraper = EAuksionScraper(ScraperOptions())
    lots = await scraper.run()
    print(f"Found {len(lots)} lots")
    for lot in lots[:5]:
        print(lot)
    await scraper.close()

if __name__ == '__main__':
    asyncio.run(run())
