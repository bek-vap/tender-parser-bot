import json

with open("scratch/trade_486901_full.json", "r", encoding="utf-8") as f:
    data = json.load(f)

print("=== Inspection of Completed Trade 486901 ===")
for key in ['consider', 'customer_name', 'delivering_phone', 'seller_id']:
    val = data.get(key)
    print(f"\nKey '{key}':")
    if isinstance(val, (dict, list)):
        print(json.dumps(val, indent=2, ensure_ascii=False))
    else:
        print(val)
        
# Let's print out all keys that contain a list of dicts, which might have seller/winner info
print("\n=== Inspecting all list fields for winner info ===")
for k, v in data.items():
    if isinstance(v, list) and v:
        print(f"\nList key: {k} (length={len(v)})")
        print(json.dumps(v[:2], indent=2, ensure_ascii=False))
    elif isinstance(v, str) and ("[" in v or "{" in v):
        try:
            parsed = json.loads(v)
            if isinstance(parsed, list) and parsed:
                print(f"\nParsed string-list key: {k} (length={len(parsed)})")
                print(json.dumps(parsed[:2], indent=2, ensure_ascii=False))
        except:
            pass
