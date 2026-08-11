import asyncio, json
import sys
import os

# Ensure backend_py is in the python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.scrapers.tender_mc import TenderMcScraper

async def main():
    scraper = TenderMcScraper()
    lots = await scraper.run()
    print('Scraped', len(lots), 'lots from Tender MC')
    
    data = []
    for lot in lots:
        data.append({
            'external_id': getattr(lot, 'external_id', None),
            'title': getattr(lot, 'title', None),
            'amount': getattr(lot, 'amount', None),
            'region': getattr(lot, 'region', None),
            'url': getattr(lot, 'url', None),
            'organizer_name': getattr(lot, 'organizer_name', None),
        })
    
    with open('scratch/tender_mc_results.json', 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
        
    print("Wrote results to scratch/tender_mc_results.json")

if __name__ == '__main__':
    asyncio.run(main())
