
import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()
from arab.models import Word

def check():
    with open('check_result.txt', 'w', encoding='utf-8') as f:
        f.write("Checking bad entries...\n")
        # Find and Delete
        bad_words = Word.objects.filter(translation_uz__icontains="alternative spelling")
        count = bad_words.count()
        f.write(f"Bad entries count: {count}\n")
        
        if count > 0:
            bad_words.delete()
            f.write(f"Deleted {count} bad entries.\n")

        f.write("Checking specific translations:\n")
        for w in Word.objects.filter(translation_uz__icontains="Kostyum"):
            f.write(f" - {w.arabic}: {w.translation_uz}\n")
        for w in Word.objects.filter(translation_uz__icontains="Sharq"):
            f.write(f" - {w.arabic}: {w.translation_uz}\n")
            
        f.write(f"Total Words: {Word.objects.count()}\n")

if __name__ == '__main__':
    check()
