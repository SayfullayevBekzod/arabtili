import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from arab.models import Word

print("Checking Word model...")
try:
    count = Word.objects.count()
    print(f"Total words: {count}")
    
    if count > 0:
        first = Word.objects.first()
        print(f"First word: {first}")
        print(f"Arabic: {first.arabic}")
        print(f"Transliteration: {first.transliteration}")
        print(f"Translation UZ: {first.translation_uz}")
        print(f"Translation RU: {first.translation_ru}")
        print(f"Category: {first.category}")
        print(f"Lesson: {first.lesson}")
    else:
        print("No words found.")
        
except Exception as e:
    print(f"CRASH: {e}")
