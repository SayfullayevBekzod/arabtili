import json
try:
    with open('d:/Work/arab/words_2000_mixed_unique.json', 'r', encoding='utf-8') as f:
        data = json.load(f)
    print(f"JSON Count: {len(data)}")
except Exception as e:
    print(e)
