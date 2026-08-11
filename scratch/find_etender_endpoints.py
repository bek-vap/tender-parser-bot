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
    try:
        with httpx.Client(timeout=5.0) as client:
            resp = client.get(url, headers=headers)
            if resp.status_code == 200:
                print(f"\n🎉 SUCCESS: {url}")
                data = resp.json()
                print(json.dumps(data, indent=2, ensure_ascii=False)[:800])
                return True
            elif resp.status_code != 404:
                print(f"Status {resp.status_code}: {url}")
    except Exception as e:
        pass
    return False

if __name__ == "__main__":
    trade_id = 486901
    
    # Large list of potential endpoints
    endpoints = [
        f"https://apietender.uzex.uz/api/common/GetBids/{trade_id}",
        f"https://apietender.uzex.uz/api/common/GetBids/{trade_id}/0",
        f"https://apietender.uzex.uz/api/common/GetTradeBids/{trade_id}",
        f"https://apietender.uzex.uz/api/common/GetProposals/{trade_id}",
        f"https://apietender.uzex.uz/api/common/GetTradeProposals/{trade_id}",
        f"https://apietender.uzex.uz/api/common/GetMembers/{trade_id}",
        f"https://apietender.uzex.uz/api/common/GetTradeMembers/{trade_id}",
        f"https://apietender.uzex.uz/api/common/GetWinnersList/{trade_id}",
        f"https://apietender.uzex.uz/api/common/GetTradeWinners/{trade_id}",
        f"https://apietender.uzex.uz/api/common/GetWinners/{trade_id}",
        f"https://apietender.uzex.uz/api/common/GetProtocol/{trade_id}",
        f"https://apietender.uzex.uz/api/common/GetTradeProtocol/{trade_id}",
        f"https://apietender.uzex.uz/api/common/GetTradeWinnersList/{trade_id}",
        f"https://apietender.uzex.uz/api/common/GetOffers/{trade_id}",
        f"https://apietender.uzex.uz/api/common/GetTradeOffers/{trade_id}",
        f"https://apietender.uzex.uz/api/common/GetResults/{trade_id}",
        f"https://apietender.uzex.uz/api/common/GetTradeResults/{trade_id}",
    ]
    
    print("Testing endpoints...")
    for ep in endpoints:
        test_endpoint(ep)
    print("Finished.")
