import json

with open("scratch/trade_488000_full.json", "r", encoding="utf-8") as f:
    data = json.load(f)

# Let's print out all values of keys containing 'seller' or 'winner'
print("=== Searching in full JSON ===")
for k in data:
    val = data[k]
    val_str = str(val)
    if "seller" in k.lower() or "winner" in k.lower() or "18800" in val_str:
        print(f"{k}: {val}")
