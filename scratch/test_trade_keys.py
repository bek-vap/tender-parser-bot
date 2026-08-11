import httpx
import json
import sys

sys.stdout.reconfigure(encoding='utf-8')

headers = {
    "accept": "application/json",
    "content-type": "application/json; charset=UTF-8",
    "origin": "https://etender.uzex.uz",
    "referer": "https://etender.uzex.uz/",
    "language": "uzb",
    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
}

if __name__ == "__main__":
    trade_id = 489049
    url = f"https://apietender.uzex.uz/api/common/GetTrade/{trade_id}/0"
    with httpx.Client(timeout=15.0) as client:
        resp = client.get(url, headers=headers)
        data = resp.json()
        
        # Save a pretty printed copy of all keys and values to inspect
        print("=== Trade General Fields ===")
        print(f"Status Name: {data.get('status_name')}")
        print(f"Deal Status: {data.get('deal_status')}")
        print(f"Seller ID: {data.get('seller_id')}")
        print(f"Customer Name: {data.get('customer_name')}")
        print(f"Customer TIN: {data.get('customer_tin')}")
        
        print("\n=== Checking subfields ===")
        # Look for consider, products, budget_products
        for key in ['consider', 'products', 'budget_products']:
            val = data.get(key)
            if val:
                print(f"\nKey: {key}")
                print(json.dumps(val, indent=2, ensure_ascii=False)[:1000])
