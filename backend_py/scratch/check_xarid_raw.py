import requests
import json

headers = {
    "accept": "application/json",
    "content-type": "application/json; charset=UTF-8",
    "language": "uz",
    "referer": "https://xarid.uzex.uz/",
    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

payload = {
    "region_ids": [],
    "Is_On_Discussion": 0,
    "from": 1,
    "to": 5
}

try:
    resp = requests.post("https://xarid-api-purchase.uzex.uz/Common/GetDirectPurchases", headers=headers, json=payload, timeout=15)
    if resp.status_code == 200:
        items = resp.json()
        print("Scraped", len(items), "items")
        if items:
            print("First item keys and values:")
            print(json.dumps(items[0], indent=2, ensure_ascii=False))
    else:
        print("Status code:", resp.status_code)
except Exception as e:
    print("Error:", e)
