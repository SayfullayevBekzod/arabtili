
import os
import django
import re

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from arab.models import Word

# EXTENDED DICTIONARY
DICT_EN_UZ = {
    # VERBS (Common from Wiktionary)
    "to write": "Yozmoq", "write": "Yozmoq",
    "to read": "O'qimoq", "read": "O'qimoq",
    "to speak": "Gapirmoq", "speak": "Gapirmoq",
    "to eat": "Yemoq", "eat": "Yemoq",
    "to drink": "Ichmoq", "drink": "Ichmoq",
    "to go": "Bormoq", "go": "Bormoq",
    "to come": "Kelmoq", "come": "Kelmoq",
    "to sit": "O'tirmoq", "sit": "O'tirmoq",
    "to stand": "Turmoq", "stand": "Turmoq",
    "to see": "Ko'rmoq", "see": "Ko'rmoq",
    "to look": "Qaramoq", "look": "Qaramoq",
    "to know": "Bilmoq", "know": "Bilmoq",
    "to think": "O'ylamoq", "think": "O'ylamoq",
    "to make": "Yasamoq", "make": "Yasamoq",
    "to do": "Qilmoq", "do": "Qilmoq",
    "to take": "Olmoq", "take": "Olmoq",
    "to give": "Bermoq", "give": "Bermoq",
    "to want": "Xohlamoq", "want": "Xohlamoq",
    "to love": "Sevmoq", "love": "Sevmoq",
    "to live": "Yashamoq", "live": "Yashamoq",
    "to die": "O'lmoq", "die": "O'lmoq",
    "to work": "Ishlamoq", "work": "Ishlamoq",
    "to play": "O'ynamoq", "play": "O'ynamoq",
    "to run": "Yugurmoq", "run": "Yugurmoq",
    "to walk": "Yurmoq", "walk": "Yurmoq",
    "to hear": "Eshitmoq", "hear": "Eshitmoq",
    "to say": "Aytmoq", "say": "Aytmoq",
    "to tell": "Aytib bermoq", "tell": "Aytib bermoq",
    "to ask": "So'ramoq", "ask": "So'ramoq",
    "to answer": "Javob bermoq", "answer": "Javob bermoq",
    "to help": "Yordam bermoq", "help": "Yordam bermoq",
    "to sleep": "Uxlamoq", "sleep": "Uxlamoq",
    "to wake": "Uyg'onmoq", "wake": "Uyg'onmoq",
    "to understand": "Tushunmoq", "understand": "Tushunmoq",
    "to learn": "O'rganmoq", "learn": "O'rganmoq",
    "to teach": "O'rgatmoq", "teach": "O'rgatmoq",
    
    # ADJECTIVES
    "good": "Yaxshi", "bad": "Yomon",
    "big": "Katta", "small": "Kichik",
    "new": "Yangi", "old": "Eski",
    "young": "Yosh", "strong": "Kuchli", "weak": "Kuchsiz",
    "beautiful": "Chiroyli", "ugly": "Xunuk",
    "happy": "Xursand", "sad": "Xafa",
    "rich": "Boy", "poor": "Kambag'al",
    "hot": "Issiq", "cold": "Sovuq",
    "high": "Baland", "low": "Past",
    "long": "Uzun", "short": "Qisqa",
    "wide": "Keng", "narrow": "Tor",
    "heavy": "Og'ir", "light": "Yengil",
    "dark": "Qorong'i", "bright": "Yorug'",
    "right": "O'ng/To'g'ri", "left": "Chap",
    "true": "Rost", "false": "Yolg'on",
    
    # NOUNS (Common)
    "man": "Erkak", "woman": "Ayol", "boy": "Bola", "girl": "Qiz",
    "child": "Bola", "person": "Odam", "friend": "Do'st",
    "family": "Oilasi", "house": "Uy", "home": "Uy",
    "school": "Maktab", "student": "Talaba", "teacher": "O'qituvchi",
    "book": "Kitob", "pen": "Ruchka", "paper": "Qog'oz",
    "water": "Suv", "food": "Ovqat", "bread": "Non", "meat": "Go'sht",
    "milk": "Sut", "tea": "Choy", "coffee": "Qahva",
    "apple": "Olma", "fruit": "Meva",
    "city": "Shahar", "country": "Davlat", "world": "Dunyo",
    "sun": "Quyosh", "moon": "Oy", "sky": "Osmon", "star": "Yulduz",
    "day": "Kun", "night": "Tun", "morning": "Erta", "evening": "Kech",
    "time": "Vaqt", "year": "Yil", "month": "Oy", "week": "Hafta",
    "money": "Pul", "car": "Mashina", "road": "Yo'l",
    "language": "Til", "word": "So'z", "name": "Ism",
    "hand": "Qo'l", "foot": "Oyoq", "head": "Bosh", "eye": "Ko'z",
    "ear": "Quloq", "mouth": "Og'iz", "nose": "Burun",
    "heart": "Yurak", "blood": "Qon", "body": "Tana",
    "god": "Xudo/Alloh", "religion": "Din", "prayer": "Namoz",
    "life": "Hayot", "death": "O'lim", "peace": "Tinchlik",
    "war": "Urush",
    
    # SPECIFIC FROM USER
    "confess": "Tan olmoq", "admit": "Tan olmoq",
    "travel": "Sayohat qilmoq", 
    "take by force": "Zo'rlab olmoq", "rape": "Zo'rlamoq",
    "suffer indigestion": "Hazm qilolmaslik",
    "be emaciated": "Ozg'in bo'lmoq", "lose weight": "Vazn yo'qotmoq", "grow thin": "Oziqmoq",
    "brand": "Brend", "blaze": "Yog'du",
    "suit": "Kostyum",
    "overpass": "Ko'prik",
}

def finalize():
    print("Finalizing translations...")
    deleted = 0
    updated = 0
    
    update_list = []
    
    words = Word.objects.exclude(category__name='Quran')
    
    for w in words:
        orig = w.translation_uz
        if not orig:
            w.delete()
            deleted += 1
            continue
            
        clean = orig.replace("[EN] ", "").replace("Fe'l: ", "").strip()
        clean_lower = clean.lower()
        
        # 1. Direct Lookup
        if clean_lower in DICT_EN_UZ:
            w.translation_uz = DICT_EN_UZ[clean_lower]
            update_list.append(w)
            updated += 1
            continue
            
        # 2. Split by comma and try first word
        parts = [p.strip() for p in clean.split(',')]
        if len(parts) > 0 and parts[0].lower() in DICT_EN_UZ:
             w.translation_uz = DICT_EN_UZ[parts[0].lower()]
             update_list.append(w)
             updated += 1
             continue
             
        # 3. Handle "be X" or "to X"
        if clean_lower.startswith("be ") and clean_lower[3:] in DICT_EN_UZ:
             w.translation_uz = DICT_EN_UZ[clean_lower[3:]] + " bo'lmoq"
             update_list.append(w)
             updated += 1
             continue
             
        # 4. If still English -> DELETE
        # Heuristic: looks exactly like original english or contains [EN] or Fe'l
        # If the word is NOT in our dictionary and we couldn't translate it,
        # checking if it is already Uzbek is hard.
        # But since we bulk imported English, most are English.
        if "[EN]" in orig or "Fe'l" in orig:
             w.delete()
             deleted += 1
        elif any(x in clean for x in ['the', 'and', 'of', 'to', 'a', 'in']): # English stopwords
             w.delete()
             deleted += 1
        # Else assumes it might be Uzbek (manual entry?) or accepted.
        
    Word.objects.bulk_update(update_list, ['translation_uz'])
    print(f"Updated: {updated} words.")
    print(f"Deleted: {deleted} remaining English words.")
    print(f"Remaining Words: {Word.objects.count()}")

if __name__ == '__main__':
    finalize()
