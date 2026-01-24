import csv
import os
from django.core.management.base import BaseCommand
from django.db import transaction
from arab.models import Word, VocabularyCategory

class Command(BaseCommand):
    help = 'Imports words from a CSV file'

    def add_arguments(self, parser):
        parser.add_argument('csv_file', type=str, help='Path to the CSV file')

    def handle(self, *args, **options):
        csv_path = options['csv_file']
        
        if not os.path.exists(csv_path):
            self.stdout.write(self.style.ERROR(f'File not found: {csv_path}'))
            return

        with open(csv_path, 'r', encoding='utf-8') as f:
            reader = csv.reader(f)
            # Skip header if it exists
            first_row = next(reader, None)
            if first_row and first_row[0] == 'word_uz':
                pass # Skip
            else:
                # If first row is not header, we need to process it
                # But typically we expect a header. Let's just reset or handle it.
                f.seek(0)
                reader = csv.reader(f)

            with transaction.atomic():
                created_count = 0
                updated_count = 0
                category_cache = {}

                for row in reader:
                    if not row or len(row) < 6:
                        continue
                    
                    # Some rows might be headers again if user copy-pasted multiple times
                    if row[0] == 'word_uz':
                        continue

                    uz_word, arabic, mean_uz, mean_ru, cat_name, w_type = row[:6]
                    
                    if not arabic:
                        continue

                    if cat_name not in category_cache:
                        category, _ = VocabularyCategory.objects.get_or_create(name=cat_name)
                        category_cache[cat_name] = category
                    
                    category = category_cache[cat_name]

                    word, created = Word.objects.update_or_create(
                        arabic=arabic,
                        defaults={
                            'translation_uz': mean_uz,
                            'translation_ru': mean_ru,
                            'category': category,
                            'word_type': w_type,
                            'transliteration': uz_word
                        }
                    )
                    if created:
                        created_count += 1
                    else:
                        updated_count += 1

        self.stdout.write(self.style.SUCCESS(f'Successfully processed CSV. Created {created_count}, Updated {updated_count}.'))
