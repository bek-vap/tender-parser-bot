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
    seller_id = 114027
    
    endpoints = [
        f"https://apietender.uzex.uz/api/common/GetDeal/{trade_id}",
        f"https://apietender.uzex.uz/api/common/GetDeal/{trade_id}/0",
        f"https://apietender.uzex.uz/api/common/GetContract/{trade_id}",
        f"https://apietender.uzex.uz/api/common/GetContract/{trade_id}/0",
        f"https://apietender.uzex.uz/api/common/GetSeller/{seller_id}",
        f"https://apietender.uzex.uz/api/common/GetSellerProfile/{seller_id}",
        f"https://apietender.uzex.uz/api/common/GetSellerProfile?sellerId={seller_id}",
        f"https://apietender.uzex.uz/api/common/GetSellerInfo/{seller_id}",
        f"https://apietender.uzex.uz/api/common/GetSellerInfo?sellerId={seller_id}",
        f"https://apietender.uzex.uz/api/common/GetOrganization/{seller_id}",
        f"https://apietender.uzex.uz/api/common/GetOrganization?orgId={seller_id}",
    ]
    
    print("Testing deal and seller endpoints...")
    for ep in endpoints:
        test_endpoint(ep)
    print("Finished.")
