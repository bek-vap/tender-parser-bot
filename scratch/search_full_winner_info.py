import json

with open("scratch/trade_486901_full.json", "r", encoding="utf-8") as f:
    data = json.load(f)

def search_nested(obj, target, path="root"):
    if isinstance(obj, dict):
        for k, v in obj.items():
            new_path = f"{path}->{k}"
            if str(v) == str(target):
                print(f"Match found at: {new_path} (value={v})")
            elif str(target) in str(v):
                print(f"Partial match found in key: {new_path}")
                if isinstance(v, (str, int, float, bool)):
                    print(f"  Value: {v}")
            search_nested(v, target, new_path)
    elif isinstance(obj, list):
        for idx, item in enumerate(obj):
            new_path = f"{path}[{idx}]"
            if str(item) == str(target):
                print(f"Match found at: {new_path} (value={item})")
            search_nested(item, target, new_path)

if __name__ == "__main__":
    search_nested(data, 114027)
