import asyncio
import json
import sys
from app.services.lot_search_service import get_lot_search_service

async def main():
    # Reconfigure stdout to use UTF-8 to prevent Windows terminal crashes on Uzbek characters
    sys.stdout.reconfigure(encoding='utf-8')
    
    service = get_lot_search_service()
    lot_id = "484088"
    print(f"[*] Testing search_lot_everywhere for lot {lot_id}...")
    
    result = await service.search_lot_everywhere(lot_id)
    if result:
        print("[+] SUCCESS! Got result via API:")
        print(json.dumps(result, indent=2, ensure_ascii=False))
    else:
        print("[-] FAILED: No data returned.")

if __name__ == "__main__":
    asyncio.run(main())
