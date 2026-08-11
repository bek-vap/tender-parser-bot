import sys, os, asyncio, json
# Ensure project root is on sys.path
project_root = r"d:/My Projects/TENDER-INTELLIGENCE-PLATFORM/backend_py"
if project_root not in sys.path:
    sys.path.append(project_root)

from app.scrapers.e_auksion import EAuksionScraper

async def main():
    scraper = EAuksionScraper()
    lots = await scraper.scrape_lots()
    print('Scraped', len(lots), 'lots')
    if lots:
        lot = lots[0]
        print('First lot fields:')
        print(json.dumps({
            'external_id': lot.external_id,
            'title': lot.title,
            'amount': lot.amount,
            'region': lot.region,
            'url': lot.url,
            'organizer_name': lot.organizer_name,
            'organizer_phone': lot.organizer_phone,
        }, ensure_ascii=False, indent=2))
    await scraper.close()

if __name__ == '__main__':
    asyncio.run(main())
