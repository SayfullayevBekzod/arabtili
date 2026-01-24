
import gzip
import json

WIKTIONARY_GZ = "wiktionary_raw.jsonl.gz"

def inspect():
    print(f"Inspecting {WIKTIONARY_GZ}...")
    try:
        with gzip.open(WIKTIONARY_GZ, "rt", encoding="utf-8") as f:
            for i, line in enumerate(f):
                if i > 20: break
                
                try:
                    obj = json.loads(line)
                except: continue

                if obj.get("lang") != "Arabic": continue

                # Print key fields to find vocalization
                print("\n--- WORD ---")
                print("ID:", i)
                print("Word (Title):", obj.get("word"))
                
                # Check forms for diacritics
                vocalized = None
                if "forms" in obj:
                    for f in obj["forms"]:
                        val = f.get("form", "")
                        # Check for tashkeel chars range 064B-0652 + Shadda 0651 + Sukun 0652
                        # Typical range for decorative: 064B-065F
                        if any('\u064b' <= c <= '\u065f' for c in val):
                            print(f"   -> Found Vocalized: {val} (Tags: {f.get('tags')})")
                            vocalized = val
                
                if vocalized:
                     print(f"   MATCH: {obj.get('word')} -> {vocalized}")
                
                # Check sounds
                if "sounds" in obj:
                    print("Sounds:", json.dumps(obj["sounds"], ensure_ascii=False))

                # Check head templates?
                
    except Exception as e:
        print(e)

if __name__ == '__main__':
    inspect()
