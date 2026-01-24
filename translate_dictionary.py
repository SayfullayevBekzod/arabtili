
import os
import django
import re

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from arab.models import Word

# Manual dictionary for common words (Best effort top 500 equivalent)
TRANSLATIONS = {
    # Pronouns
    "I": "Men", "you": "Sen", "he": "U", "she": "U", "it": "U", "we": "Biz", "they": "Ular",
    "this": "Bu", "that": "Anavi", "who": "Kim", "what": "Nima",
    
    # Common Nouns
    "water": "Suv", "fire": "Olov", "earth": "Yer", "air": "Havo",
    "book": "Kitob", "pen": "Qalam", "paper": "Qog'oz", "school": "Maktab",
    "house": "Uy", "door": "Eshik", "window": "Deraza", "room": "Xona",
    "man": "Erkak", "woman": "Ayol", "boy": "Bola", "girl": "Qiz",
    "father": "Ota", "mother": "Ona", "brother": "Aka/Uka", "sister": "Opa/Singil",
    "sun": "Quyosh", "moon": "Oy", "star": "Yulduz", "sky": "Osmon",
    "day": "Kun", "night": "Tun", "morning": "Tong", "evening": "Oqshom",
    "time": "Vaqt", "year": "Yil", "month": "Oy", "week": "Hafta",
    "hand": "Qo'l", "foot": "Oyoq", "head": "Bosh", "eye": "Ko'z",
    "heart": "Yurak", "life": "Hayot", "death": "O'lim",
    "king": "Podshoh", "queen": "Qirolicha", "president": "Prezident",
    "city": "Shahar", "village": "Qishloq", "country": "Mamlakat",
    "language": "Til", "word": "So'z", "name": "Ism",
    "peace": "Tinchlik", "war": "Urush", "love": "Sevgi",
    "dog": "It", "cat": "Mushuk", "horse": "Ot", "camel": "Tuya",
    "fish": "Baliq", "bird": "Qush", "tree": "Daraxt", "flower": "Gul",
    "milk": "Sut", "bread": "Non", "meat": "Go'sht", "fruit": "Meva",
    
    # Adjectives
    "big": "Katta", "small": "Kichik", "new": "Yangi", "old": "Eski",
    "good": "Yaxshi", "bad": "Yomon", "beautiful": "Chiroyli", "ugly": "Xunuk",
    "hot": "Issiq", "cold": "Sovuq", "white": "Oq", "black": "Qora",
    "red": "Qizil", "green": "Yashil", "blue": "Ko'k", "yellow": "Sariq",
    
    # Verbs (Base forms)
    "to write": "Yozmoq", "to read": "O'qimoq", "to speak": "Gapirmoq",
    "to eat": "Yemoq", "to drink": "Ichmoq", "to sleep": "Uxlamoq",
    "to go": "Bormoq", "to come": "Kelmoq", "to sit": "O'tirmoq",
    "to stand": "Turmoq", "to see": "Ko'rmoq", "to know": "Bilmoq",
    
    # Islam terms (often found in Wiktionary as English definitions)
    "God": "Alloh", "religion": "Din", "prayer": "Ibodat/Namoz",
    "prophet": "Payg'ambar", "mosque": "Masjid", "paradise": "Jannat",
    "hell": "Do'zax", "sin": "Gunoh", "faith": "Iymon",
}

def clean_uz_translation(text):
    if not text: return ""
    
    # Check exact match
    if text in TRANSLATIONS:
        return TRANSLATIONS[text]
    
    # Normalize
    t_lower = text.lower().strip()
    if t_lower in TRANSLATIONS:
        return TRANSLATIONS[t_lower]
        
    # Heuristics
    # Remove "verbal noun of"
    if "verbal noun of" in t_lower:
        # Extract the arabic word if present
        match = re.search(r"verbal noun of\s+(.*?)\s+\(", t_lower)
        if match:
             return f"{match.group(1)} ning harakat nomi"
        return "Harakat nomi (Verbal Noun)"

    # Handle "to [verb]" pattern
    if t_lower.startswith("to "):
        verb = t_lower[3:]
        # Simple lookup for the verb part
        if verb in TRANSLATIONS:
             return TRANSLATIONS[verb]
        # Generic fallback for unmapped verbs: Keep English but label it?
        # Or better -> "fe'l: " + verb
        return f"Fe'l: {verb}"

    # Handle "plural of" (though we filtered these out mostly, some might remain)
    
    return f"[EN] {text}" # Prefix with [EN] if no translation found, so user knows

def apply_translations():
    count = 0
    translated = 0
    words = Word.objects.exclude(category__name='Quran') # Quran words likely handled separately? No, imported as Basic mostly.
    
    full_count = words.count()
    print(f"Processing {full_count} words...")
    
    updates = []
    
    for w in words:
        orig = w.translation_uz
        if not orig: continue
        
        # Skip if already looks Uzbek (has special chars o' g' or not English?)
        # But our import set them to English.
        
        new_trans = clean_uz_translation(orig)
        if new_trans != orig:
            w.translation_uz = new_trans
            updates.append(w)
            if not new_trans.startswith("[EN]"):
                translated += 1
        
        count += 1
        if count % 200 == 0:
            print(f"Processed {count}...")

    Word.objects.bulk_update(updates, ['translation_uz'], batch_size=100)
    print(f"Updated {len(updates)} words. Translated: {translated} (others marked [EN])")

if __name__ == '__main__':
    apply_translations()
