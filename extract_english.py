
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from arab.models import Word

def extract():
    glosses = set()
    # Only get words where translation is likely English (check if it contains latin characters? or just all)
    # Since I just imported, all 'translation_uz' are English glosses.
    for w in Word.objects.all():
        if w.translation_uz:
            glosses.add(w.translation_uz)
    
    with open('english_glosses.txt', 'w', encoding='utf-8') as f:
        for g in sorted(glosses):
            f.write(g + "\n")
    
    print(f"Extracted {len(glosses)} unique glosses from DB.")

if __name__ == '__main__':
    extract()
