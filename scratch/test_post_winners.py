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
    url = "https://apietender.uzex.uz/api/common/GetWinners"
    
    # Test POST request with various formats
    payloads = [
        {"tradeId": trade_id},
        {"trade_id": trade_id},
        {"Id": trade_id},
        [trade_id]
    ]
    
    with httpx.Client(timeout=10.0) as client:
        for p in payloads:
            print(f"\nPOST payload: {p}")
            try:
                resp = client.post(url, headers=headers, json=p)
                print(f"Status: {resp.status_code}")
                if resp.status_code == 200:
                    print(json.dumps(resp.json(), indent=2, ensure_ascii=False))
                    break
                else:
                    print(resp.text[:200])
            except Exception as e:
                print(f"Error: {e}")
