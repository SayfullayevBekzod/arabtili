
import json
import glob
import os
from datetime import datetime

def patch_file(filepath):
    print(f"Patching {filepath}...")
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        updated = False
        if isinstance(data, list):
            for item in data:
                if 'fields' in item:
                    fields = item['fields']
                    if 'created_at' not in fields:
                        fields['created_at'] = "2024-01-01T00:00:00Z"
                        updated = True
                    if 'updated_at' not in fields:
                        fields['updated_at'] = "2024-01-01T00:00:00Z"
                        updated = True
        
        if updated:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            print("  -> Updated.")
        else:
            print("  -> No changes needed.")
            
    except Exception as e:
        print(f"  -> Error: {e}")

# Patch all json files in arab/fixtures
for file in glob.glob("arab/fixtures/*.json"):
    patch_file(file)
