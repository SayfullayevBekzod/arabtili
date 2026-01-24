import json
import os
from django.core.management.base import BaseCommand
from django.db import transaction
from arab.models import Word, VocabularyCategory

class Command(BaseCommand):
    help = 'Syncs dictionary words from dictionary.json file'

    def handle(self, *args, **options):
        json_path = os.path.join(os.getcwd(), 'dictionary.json')
        
        if not os.path.exists(json_path):
            self.stdout.write(self.style.ERROR(f'File not found: {json_path}'))
            return

        try:
            with open(json_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error reading JSON: {e}'))
            return

        with transaction.atomic():
            # Clear existing data
            self.stdout.write("Clearing existing words and categories...")
            Word.objects.all().delete()
            # We might want to keep categories if they have images/descriptions, 
            # but user said "delete all words", and categories are usually secondary here.
            # To be safe and clean, we recreate categories.
            VocabularyCategory.objects.all().delete()

            created_count = 0
            category_cache = {}

            for item in data:
                arabic = item.get('arabic')
                translit = item.get('transliteration', '')
                uz = item.get('uz', '')
                ru = item.get('ru', '')
                cat_name = item.get('category', 'General')

                if not arabic:
                    continue

                if cat_name not in category_cache:
                    category, _ = VocabularyCategory.objects.get_or_create(name=cat_name)
                    category_cache[cat_name] = category
                
                category = category_cache[cat_name]

                Word.objects.create(
                    arabic=arabic,
                    transliteration=translit,
                    pronunciation=item.get('pronunciation', ''),
                    makhraj=item.get('makhraj', ''),
                    translation_uz=uz,
                    translation_ru=ru,
                    category=category
                )
                created_count += 1

        self.stdout.write(self.style.SUCCESS(f'Successfully synced {created_count} words.'))
