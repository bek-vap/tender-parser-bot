import asyncio, json
import sys
import os

# Ensure backend_py is in the python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.scrapers.e_auksion import EAuksionScraper

async def main():
    scraper = EAuksionScraper()
    lots = await scraper.scrape_lots()
    print('Scraped', len(lots), 'lots')
    
    data = []
    for lot in lots:
        data.append({
            'external_id': lot.external_id,
            'title': lot.title,
            'amount': lot.amount,
            'region': lot.region,
            'url': lot.url,
            'organizer_name': lot.organizer_name,
            'organizer_phone': lot.organizer_phone,
        })
    
    with open('scratch/results.json', 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
        
    print("Wrote results to scratch/results.json")
    await scraper.close()

if __name__ == '__main__':
    asyncio.run(main())
