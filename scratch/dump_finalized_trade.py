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
    trade_id = 486901
    url = f"https://apietender.uzex.uz/api/common/GetTrade/{trade_id}/0"
    with httpx.Client(timeout=15.0) as client:
        resp = client.get(url, headers=headers)
        data = resp.json()
        
        with open("scratch/trade_486901_full.json", "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
            
        print("Successfully dumped full trade 486901 details to scratch/trade_486901_full.json")
        
        # Search for any sign of the winner company name or details in all fields
        print("\n=== Non-empty fields ===")
        for k, v in data.items():
            if v is not None and v != "" and v != [] and v != "[]":
                val_str = str(v)
                if len(val_str) > 200:
                    val_str = val_str[:200] + "..."
                print(f"  {k}: {val_str}")
