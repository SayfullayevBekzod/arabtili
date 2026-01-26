
import os
import django
import json

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from arab.models import Word, VocabularyCategory

def run():
    with open('words_new.json', 'r', encoding='utf-8') as f:
        data = json.load(f)
        
    created_count = 0
    for item in data:
        cat_name = item.get('category', 'General')
        category, _ = VocabularyCategory.objects.get_or_create(name=cat_name)
        
        # Check if exists
        word, created = Word.objects.get_or_create(
            arabic=item['arabic'],
            defaults={
                'transliteration': item.get('transliteration', ''),
                'translation_uz': item.get('translation_uz', ''),
                'translation_ru': item.get('translation_ru', ''),
                'category': category
            }
        )
        
        if created:
            created_count += 1
            print(f"Created: {word.arabic}")
        else:
            print(f"Skipped (exists): {word.arabic}")
            
    print(f"Finished! Added {created_count} new words.")

if __name__ == '__main__':
    run()
