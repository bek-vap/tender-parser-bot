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
    for trade_id in [486901, 486870, 486863]:
        url = f"https://apietender.uzex.uz/api/common/GetWinners?tradeId={trade_id}"
        print(f"\nQuerying: {url}")
        try:
            with httpx.Client(timeout=10.0) as client:
                resp = client.get(url, headers=headers)
                print(f"Status: {resp.status_code}")
                if resp.status_code == 200:
                    print(json.dumps(resp.json(), indent=2, ensure_ascii=False))
        except Exception as e:
            print(f"Error: {e}")
