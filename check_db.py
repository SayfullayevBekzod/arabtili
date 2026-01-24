
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from arab.models import Word

def check():
    count = Word.objects.count()
    print(f"Total Words in DB: {count}")
    for w in Word.objects.exclude(category__name='Quran').all()[:5]:
        print(f" - {w.arabic}: {w.translation_uz}")

if __name__ == '__main__':
    check()
