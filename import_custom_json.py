
import os
import django
import json
import sys

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
try:
    django.setup()
except Exception as e:
    print(f"Django setup failed: {e}")
    sys.exit(1)

from arab.models import Word, VocabularyCategory

def import_json(file_path):
    print(f"📂 Opening {file_path}...")
    
    if not os.path.exists(file_path):
        print(f"❌ File not found: {file_path}")
        return

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        print(f"❌ Invalid JSON: {e}")
        return
    except Exception as e:
        print(f"❌ Error reading file: {e}")
        return

    if not isinstance(data, list):
        print("❌ JSON root must be a list of objects.")
        return

    print(f"🔍 Found {len(data)} items. Starting import...")

    added = 0
    updated = 0
    errors = 0

    # Ensure default category exists
    default_cat, _ = VocabularyCategory.objects.get_or_create(name="General")

    for i, item in enumerate(data):
        try:
            # Expected fields: 'arabic', 'translation', 'transliteration' (optional), 'category' (optional)
            arabic = item.get('arabic') or item.get('word')
            translation = item.get('translation') or item.get('translation_uz') or item.get('uz') or item.get('meaning')
            
            if not arabic or not translation:
                print(f"⚠️ Skipping item {i}: Missing 'arabic' or 'translation' field.")
                errors += 1
                continue

            transliteration = item.get('transliteration', '')
            cat_name = item.get('category', 'General')
            
            # Sub-category handling
            if cat_name != "General":
                cat, _ = VocabularyCategory.objects.get_or_create(name=cat_name)
            else:
                cat = default_cat

            # Update or Create
            # We assume ARABIC uniqueness for update
            obj, created = Word.objects.update_or_create(
                arabic=arabic,
                defaults={
                    'translation_uz': translation,
                    'transliteration': transliteration,
                    'category': cat,
                }
            )

            if created:
                added += 1
            else:
                updated += 1
                
        except Exception as e:
            print(f"❌ Error on item {i} ({arabic}): {e}")
            errors += 1

    print("-" * 30)
    print(f"✅ DONE!")
    print(f"🆕 Added: {added}")
    print(f"🔄 Updated: {updated}")
    print(f"⚠️ Errors: {errors}")
    print("-" * 30)

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python import_custom_json.py <path_to_json_file>")
        print("Example: python import_custom_json.py my_words.json")
    else:
        import_json(sys.argv[1])
