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

def test_endpoint(url):
    print(f"\nQuerying: {url}")
    try:
        with httpx.Client(timeout=15.0) as client:
            resp = client.get(url, headers=headers)
            print(f"Status: {resp.status_code}")
            if resp.status_code == 200:
                data = resp.json()
                print("Success! Keys in response:")
                if isinstance(data, dict):
                    print(list(data.keys()))
                    # Look for anything like "winner", "tin", "seller"
                    for key in data:
                        if "winner" in key.lower() or "seller" in key.lower():
                            print(f"  {key}: {data[key]}")
                elif isinstance(data, list):
                    print(f"List of {len(data)} items. First item keys:")
                    if data:
                        print(list(data[0].keys()))
                return data
            else:
                print(resp.text[:200])
    except Exception as e:
        print(f"Error: {e}")
    return None

if __name__ == "__main__":
    trade_id = 489049
    # Test GetTrade/{trade_id}/0
    test_endpoint(f"https://apietender.uzex.uz/api/common/GetTrade/{trade_id}/0")
    # Test potential winner endpoints
    test_endpoint(f"https://apietender.uzex.uz/api/common/GetWinners?tradeId={trade_id}")
    test_endpoint(f"https://apietender.uzex.uz/api/common/GetTradeWinners/{trade_id}")
    test_endpoint(f"https://apietender.uzex.uz/api/common/GetWinners/{trade_id}")
