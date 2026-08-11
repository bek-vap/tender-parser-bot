import httpx
import json

def get_trade_details(trade_id):
    url = f"https://apietender.uzex.uz/api/common/GetTrade/{trade_id}/0"
    headers = {
        "accept": "application/json",
        "content-type": "application/json; charset=UTF-8",
        "origin": "https://etender.uzex.uz",
        "referer": "https://etender.uzex.uz/",
        "language": "uzb",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
    }
    
    with httpx.Client(timeout=30.0) as client:
        resp = client.get(url, headers=headers)
        print(f"Status: {resp.status_code}")
        return resp.json()

if __name__ == "__main__":
    details = get_trade_details(484088)
    import sys
    # Avoid unicode encode errors on Windows stdout
    sys.stdout.reconfigure(encoding='utf-8')
    print(json.dumps(details, indent=2, ensure_ascii=False))
