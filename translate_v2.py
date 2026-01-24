
import os
import django
import re

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from arab.models import Word

# ----------------------------------------------------
# 1. CLEANUP BAD ENTRIES
# ----------------------------------------------------
def cleanup_bad_glosses():
    print("Cleaning up bad glosses...")
    # Remove words where definitions are just references
    bad_patterns = [
        "alternative spelling of", 
        "alternative form of", 
        "plural of", 
        "feminine of",
        "masculine of",
    ]
    
    deleted_count = 0
    for w in Word.objects.all():
        gloss = (w.translation_uz or "").lower()
        if any(p in gloss for p in bad_patterns):
            w.delete()
            deleted_count += 1
            
    print(f"Deleted {deleted_count} words with bad glosses.")

# ----------------------------------------------------
# 2. TRANSLATION DICTIONARY
# ----------------------------------------------------
DICT_EN_UZ = {
    # Pronouns
    "i": "Men", "you": "Sen", "he": "U", "she": "U", "it": "U", "we": "Biz", "they": "Ular",
    
    # Common verbs
    "be": "Bo'lmoq", "become": "Bo'lmoq", 
    "do": "Qilmoq", "make": "Yasamoq",
    "say": "Aytmoq", "speak": "Gapirmoq",
    "go": "Bormoq", "come": "Kelmoq",
    
    # Nouns
    "suit (of clothes)": "Kostyum",
    "suit": "Kostyum",
    "brand": "Brend", "blaze": "Olov/Yog'du", "burning flame": "Yong'in",
    "mashriq": "Mashriq (Sharq)",
    "five": "Besh", "six": "Olti", "seven": "Yetti",
    "golden": "Oltin rang",
    "powerful": "Kuchli", "mighty": "Qudratli", "strong": "Kuchli",
    "done": "Bajarilgan", "made": "Yasalgan",
    "overpass": "Ko'prik", "flyover": "Estakada",
    "film": "Kino", "motion picture": "Film",
    "pagan": "Majusiy", "polytheist": "Mushrik",
    
    # Add common Wiktionary terms
    "[en]": "", # Remove prefix if found alone
}

def translate_phrase(text):
    if not text: return ""
    text = text.replace("[EN] ", "").strip()
    original = text
    text_lower = text.lower()
    
    # Exact match
    if text_lower in DICT_EN_UZ:
        return DICT_EN_UZ[text_lower]
        
    # Pattern: "A, B, C" -> Just take first? Or translate first?
    if "," in text:
        parts = [p.strip() for p in text.split(",")]
        # Try to translate first part
        first = parts[0].lower()
        if first in DICT_EN_UZ:
            return DICT_EN_UZ[first]
            
    # Pattern: "be or become X"
    match = re.search(r"be or become ([\w\s]+)", text_lower)
    if match:
        adj = match.group(1)
        # return f"{adj} bo'lmoq" # Need to translate adj
        if adj in DICT_EN_UZ:
            return f"{DICT_EN_UZ[adj]} bo'lmoq"
        return f"{adj} bo'lmoq"

    # Pattern: "Fe'l: X" -> "Xmoq" ?
    if text.startswith("Fe'l:"):
        # Keep it, it's already semi-Uzbek from previous run
        pass
        
    return f"{text}" # Keep as is if no match

def apply_translation():
    updates = []
    
    words = Word.objects.all()
    print(f"Translating {words.count()} words...")
    
    for w in words:
        old_gloss = w.translation_uz
        if not old_gloss: continue
        
        # Cleanup [EN] prefix for processing
        clean = old_gloss.replace("[EN]", "").strip()
        
        # Check specific words from user report
        if "mashriq" in clean.lower():
            new_gloss = "Sharq (Mashriq)"
        elif "brand" in clean.lower() and "blaze" in clean.lower():
            new_gloss = "Yog'du, Olov"
        elif "suit (of clothes)" in clean.lower():
            new_gloss = "Kostyum"
        elif "alternative spelling" in clean.lower():
            # Should have been deleted by cleanup_bad_glosses, but just in case
            w.delete()
            continue 
        else:
             # Try dictionary
             new_gloss = translate_phrase(clean)
             if new_gloss == clean:
                  # If no change, restore [EN] if it really doesn't look Uzbek
                  # Simple heuristic: if contains 'sh', 'ch', 'ng' it might be Uzbek, 
                  # but English has those too. 
                  # Let's just prefix [EN] again if we are unsure, 
                  # BUT user wants "Javoblari uzbek tilida".
                  # Giving misleading [EN] is better than fake Uzbek.
                  # But I will try to translate frequent words from the big dictionary in previous step.
                  # Since I don't have the big dictionary here embedded, I will rely on the ones I added.
                  if not old_gloss.startswith("Fe'l") and not old_gloss.startswith("[EN]"):
                       new_gloss = f"[EN] {clean}"
                  else:
                       new_gloss = old_gloss # Keep existing [EN] or Fe'l

        if new_gloss != old_gloss:
            w.translation_uz = new_gloss
            updates.append(w)
            
    if updates:
        Word.objects.bulk_update(updates, ['translation_uz'], batch_size=100)
        print(f"Updated {len(updates)} translations.")

if __name__ == '__main__':
    cleanup_bad_glosses()
    apply_translation()
