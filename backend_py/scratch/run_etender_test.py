import json
import sys
import os

# Ensure backend_py is in the python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.clients.uzex_etender_api import UzexEtenderApiClient

async def main():
    client = UzexEtenderApiClient()
    try:
        items = await client.trade_list(type_id=2, from_=1, to=10)
        print('Scraped', len(items), 'lots from etender.uzex.uz via API')
        
        data = []
        for it in items:
            data.append({
                'external_id': getattr(it, 'id', None),
                'title': getattr(it, 'name', None),
                'amount': getattr(it, 'cost', None),
                'region': getattr(it, 'region_name', None),
                'url': f"https://etender.uzex.uz/lot/{getattr(it, 'id', '')}",
                'organizer_name': getattr(it, 'seller_name', None),
                'organizer_inn': getattr(it, 'seller_tin', None),
            })
        
        with open('scratch/etender_results.json', 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
            
        print("Wrote results to scratch/etender_results.json")
    finally:
        await client.close()

if __name__ == '__main__':
    import asyncio
    asyncio.run(main())
