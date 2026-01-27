from django.core.management.base import BaseCommand
from arab.models import Word, VocabularyCategory
import json
import os
from django.conf import settings

class Command(BaseCommand):
    help = 'Import new words from words_new.json'

    def handle(self, *args, **kwargs):
        json_path = os.path.join(settings.BASE_DIR, 'words_new.json')
        if not os.path.exists(json_path):
            self.stdout.write(self.style.WARNING(f'File not found: {json_path}'))
            return

        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            
        created_count = 0
        for item in data:
            cat_name = item.get('category', 'General')
            category, _ = VocabularyCategory.objects.get_or_create(name=cat_name)
            
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
                self.stdout.write(f"Created: {word.arabic}")
        
        self.stdout.write(self.style.SUCCESS(f"Finished! Added {created_count} new words."))
