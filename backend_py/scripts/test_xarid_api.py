import asyncio
import sys
from app.scrapers.xarid_uzex import XaridUzexScraper

async def main():
    sys.stdout.reconfigure(encoding='utf-8')
    print("[*] Instantiating and running revised XaridUzexScraper (direct API)...")
    scraper = XaridUzexScraper()
    tenders = await scraper.run()
    
    print(f"\n[+] SUCCESS! Found {len(tenders)} direct purchase tenders.")
    if tenders:
        print("\nFirst 3 parsed tenders:")
        for i, t in enumerate(tenders[:3], 1):
            print(f"  {i}. ID: {t.external_id}")
            print(f"     Title: {t.title}")
            print(f"     Amount: {t.amount}")
            print(f"     Organizer: {t.organizer_name} (INN: {t.organizer_inn})")
            print(f"     URL: {t.url}")

if __name__ == "__main__":
    asyncio.run(main())
