
import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()
from arab.models import Word

def analyze():
    # Find words with English chars in translation
    # "Fe'l" is Uzbek but has latin chars. We assume English if it has longer English words.
    # Regex: [a-zA-Z] is not enough because Uzbek has Latin script.
    # Heuristic: [EN] prefix or "Fe'l: " followed by English text.
    # Or just manual inspection of random samples.
    
    qs = Word.objects.exclude(category__name='Quran')
    
    english_looking = []
    for w in qs:
        t = w.translation_uz
        # Detect if "Fe'l:" followed by English
        if t.startswith("Fe'l:"):
            english_looking.append(f"{w.arabic}: {t}")
        elif "[EN]" in t:
             english_looking.append(f"{w.arabic}: {t}")
        # Detect unmapped English words (often comma separated)
        # e.g. "go, travel"
        # Uzbek would be "bormoq, sayohat"
        
    print(f"Total Words: {qs.count()}")
    print(f"English-ish translations found: {len(english_looking)}")
    with open('remaining_english.txt', 'w', encoding='utf-8') as f:
        for l in english_looking[:200]: # Sample
            f.write(l + "\n")

if __name__ == '__main__':
    analyze()
