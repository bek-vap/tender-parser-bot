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
    start_id = 488000
    print(f"Scanning trades starting from {start_id} downwards...")
    
    with httpx.Client(timeout=10.0) as client:
        checked = 0
        found_completed = 0
        for offset in range(300):
            trade_id = start_id - offset
            url = f"https://apietender.uzex.uz/api/common/GetTrade/{trade_id}/0"
            try:
                resp = client.get(url, headers=headers)
                if resp.status_code == 200:
                    data = resp.json()
                    status = data.get("status_name") or ""
                    deal_status = data.get("deal_status")
                    seller_id = data.get("seller_id")
                    
                    # Print unique statuses
                    print(f"Trade {trade_id}: Status='{status}', DealStatus={deal_status}, SellerID={seller_id}")
                    
                    # If status contains winner identified (G'olib) or succeeded
                    if "g'olib" in status.lower() or "gʻolib" in status.lower() or "golib" in status.lower() or "состоял" in status.lower() or (seller_id and seller_id != 0 and "amalga oshmagan" not in status.lower()):
                        print(f"\n🎉 FOUND TRADE WITH WINNER: {trade_id}")
                        print(f"Status Name: {status}")
                        print(f"Seller ID: {seller_id}")
                        print(f"Customer Name: {data.get('customer_name')}")
                        
                        # Let's try to query Winners or see if there is another endpoint
                        print("Let's try to query GetWinners for this trade:")
                        win_url = f"https://apietender.uzex.uz/api/common/GetWinners?tradeId={trade_id}"
                        w_resp = client.get(win_url, headers=headers)
                        print(f"GetWinners status: {w_resp.status_code}")
                        if w_resp.status_code == 200:
                            print(json.dumps(w_resp.json(), indent=2, ensure_ascii=False))
                        
                        found_completed += 1
                        if found_completed >= 3:
                            break
            except Exception as e:
                pass
            checked += 1
