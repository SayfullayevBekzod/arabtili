
import os
import django
import json

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from arab.models import Word, VocabularyCategory

def import_real():
    # 1. Clear existing generic data
    Word.objects.all().delete()
    print("Deleted old words.")

    # 2. Load the REAL generated data
    json_path = 'd:/Work/arab/words_2000_mixed_unique.json'
    if not os.path.exists(json_path):
        print("JSON file not found.")
        return

    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    print(f"Loading {len(data)} words...")

    words_to_create = []
    categories = {}
    
    for item in data:
        cat_name = item.get('category', 'Basic')
        if cat_name not in categories:
            category, _ = VocabularyCategory.objects.get_or_create(name=cat_name)
            categories[cat_name] = category
        
        words_to_create.append(Word(
            arabic=item['arabic'],
            transliteration=item.get('transliteration', ''),
            translation_uz=item.get('uz', ''), 
            translation_ru=item.get('ru', ''),
            category=categories[cat_name]
        ))
    
    # Batch create with ignore_conflicts
    Word.objects.bulk_create(words_to_create, batch_size=100, ignore_conflicts=True)
    print(f"Successfully processed {len(words_to_create)} CLEAN words.")

if __name__ == '__main__':
    import_real()
