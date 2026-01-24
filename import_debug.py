
import os
import django
import json
import sys

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
try:
    django.setup()
    print("Django setup success.")
except Exception as e:
    print(f"Django setup failed: {e}")
    sys.exit(1)

from arab.models import Word, VocabularyCategory

def import_debug():
    print("Starting debug import...")
    
    # Check JSON
    json_path = 'd:/Work/arab/words_2000_mixed_unique.json'
    if not os.path.exists(json_path):
        print("CRITICAL: JSON file missing!")
        return

    try:
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        print(f"JSON loaded. Entries: {len(data)}")
    except Exception as e:
        print(f"JSON load failed: {e}")
        return

    # Delete existing
    try:
        cnt, _ = Word.objects.all().delete()
        print(f"Deleted {cnt} existing words.")
    except Exception as e:
        print(f"Delete failed: {e}")
        return

    # Prepare data
    words = []
    category_cache = {}
    
    # Helper for category
    def get_category(name):
        if name not in category_cache:
            c, _ = VocabularyCategory.objects.get_or_create(name=name)
            category_cache[name] = c
        return category_cache[name]

    print("Building objects...")
    for i, item in enumerate(data):
        try:
            w = Word(
                arabic=item['arabic'],
                transliteration=item.get('transliteration', '') or '',
                translation_uz=item.get('uz', ''),
                translation_ru=item.get('ru', ''),
                category=get_category(item.get('category', 'Basic'))
            )
            words.append(w)
        except Exception as e:
            print(f"Error building item {i}: {e}")

    print(f"Ready to insert {len(words)} words.")
    
    # Insert in chunks manually to catch errors
    batch_size = 100
    for i in range(0, len(words), batch_size):
        chunk = words[i:i+batch_size]
        try:
            Word.objects.bulk_create(chunk, ignore_conflicts=True)
            print(f"Inserted batch {i//batch_size + 1}")
        except Exception as e:
            print(f"Batch {i//batch_size + 1} failed: {e}")

    final_count = Word.objects.count()
    print(f"Final DB Count: {final_count}")

if __name__ == '__main__':
    import_debug()
