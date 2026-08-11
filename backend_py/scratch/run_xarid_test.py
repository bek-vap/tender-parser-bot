import asyncio, json
import sys
import os

# Ensure backend_py is in the python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.scrapers.xarid_uzex import XaridUzexScraper

async def main():
    scraper = XaridUzexScraper()
    lots = await scraper.run()
    print('Scraped', len(lots), 'lots from Xarid Uzex')
    
    data = []
    for lot in lots:
        data.append({
            'external_id': getattr(lot, 'external_id', None),
            'title': getattr(lot, 'title', None),
            'amount': getattr(lot, 'amount', None),
            'region': getattr(lot, 'region', None),
            'url': getattr(lot, 'url', None),
            'organizer_name': getattr(lot, 'organizer_name', None),
            'organizer_inn': getattr(lot, 'organizer_inn', None),
        })
    
    with open('scratch/xarid_results.json', 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
        
    print("Wrote results to scratch/xarid_results.json")

if __name__ == '__main__':
    asyncio.run(main())
