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
        with httpx.Client(timeout=10.0) as client:
            resp = client.get(url, headers=headers)
            print(f"Status: {resp.status_code}")
            if resp.status_code == 200:
                data = resp.json()
                print("Success!")
                print(json.dumps(data, indent=2, ensure_ascii=False)[:600])
                return True
    except Exception as e:
        print(f"Error: {e}")
    return False

if __name__ == "__main__":
    seller_id = 114027
    
    # Try different seller endpoints
    endpoints = [
        f"https://apietender.uzex.uz/api/common/GetSeller/{seller_id}",
        f"https://apietender.uzex.uz/api/common/GetSellerInfo/{seller_id}",
        f"https://apietender.uzex.uz/api/common/GetCompany/{seller_id}",
        f"https://apietender.uzex.uz/api/common/GetSeller?sellerId={seller_id}",
        f"https://apietender.uzex.uz/api/common/GetSellerInfo?sellerId={seller_id}",
        f"https://apietender.uzex.uz/api/common/GetMember/{seller_id}",
        f"https://apietender.uzex.uz/api/common/GetSellerDetails/{seller_id}",
        f"https://apietender.uzex.uz/api/common/GetSeller/{seller_id}/0",
        f"https://apietender.uzex.uz/api/common/GetSellerInfo/{seller_id}/0"
    ]
    
    for ep in endpoints:
        test_endpoint(ep)
