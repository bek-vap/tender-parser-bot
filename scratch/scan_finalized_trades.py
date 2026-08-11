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
    start_id = 487000
    print(f"Scanning trades starting from {start_id} downwards for finalized statuses...")
    
    with httpx.Client(timeout=10.0) as client:
        found = 0
        for offset in range(500):
            trade_id = start_id - offset
            url = f"https://apietender.uzex.uz/api/common/GetTrade/{trade_id}/0"
            try:
                resp = client.get(url, headers=headers)
                if resp.status_code == 200:
                    data = resp.json()
                    status = data.get("status_name") or ""
                    status_id = data.get("status_id")
                    deal_status = data.get("deal_status")
                    seller_id = data.get("seller_id")
                    
                    # If status_id is finalized or status indicates winner
                    # Status IDs in state procurement:
                    # 9 = G'olib aniqlangan (Winner identified)
                    # 10 = Shartnoma imzolandi (Contract signed)
                    # 11 = Savdo yakunlangan
                    # Let's print trades with status_id >= 6
                    if status_id and status_id in [7, 8, 9, 10, 11]:
                        print(f"Trade {trade_id}: Status='{status}' (ID={status_id}), DealStatus={deal_status}, SellerID={seller_id}")
                        found += 1
                        if found >= 5:
                            break
            except Exception as e:
                pass
