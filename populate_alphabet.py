import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from arab.models import Letter

ALPHABET = [
    {"name": "Alif", "arabic": "ا", "isolated": "ا", "initial": "ا", "medial": "ـا", "final": "ـا", "joins": False, "order": 1},
    {"name": "Ba", "arabic": "ب", "isolated": "ب", "initial": "بـ", "medial": "ـبـ", "final": "ـب", "joins": True, "order": 2},
    {"name": "Ta", "arabic": "ت", "isolated": "ت", "initial": "تـ", "medial": "ـتـ", "final": "ـت", "joins": True, "order": 3},
    {"name": "Tha", "arabic": "ث", "isolated": "ث", "initial": "ثـ", "medial": "ـثـ", "final": "ـث", "joins": True, "order": 4},
    {"name": "Jim", "arabic": "ج", "isolated": "ج", "initial": "جـ", "medial": "ـجـ", "final": "ـج", "joins": True, "order": 5},
    {"name": "Ha (ح)", "arabic": "ح", "isolated": "ح", "initial": "حـ", "medial": "ـحـ", "final": "ـح", "joins": True, "order": 6},
    {"name": "Kha", "arabic": "خ", "isolated": "خ", "initial": "خـ", "medial": "ـخـ", "final": "ـخ", "joins": True, "order": 7},
    {"name": "Dal", "arabic": "د", "isolated": "د", "initial": "د", "medial": "ـد", "final": "ـد", "joins": False, "order": 8},
    {"name": "Dhal", "arabic": "ذ", "isolated": "ذ", "initial": "ذ", "medial": "ـذ", "final": "ـذ", "joins": False, "order": 9},
    {"name": "Ra", "arabic": "ر", "isolated": "ر", "initial": "ر", "medial": "ـر", "final": "ـر", "joins": False, "order": 10},
    {"name": "Za", "arabic": "ز", "isolated": "ز", "initial": "ز", "medial": "ـز", "final": "ـز", "joins": False, "order": 11},
    {"name": "Seen", "arabic": "س", "isolated": "س", "initial": "سـ", "medial": "ـسـ", "final": "ـس", "joins": True, "order": 12},
    {"name": "Shin", "arabic": "ش", "isolated": "ش", "initial": "شـ", "medial": "ـشـ", "final": "ـش", "joins": True, "order": 13},
    {"name": "Sad", "arabic": "ص", "isolated": "ص", "initial": "صـ", "medial": "ـصـ", "final": "ـص", "joins": True, "order": 14},
    {"name": "Dad", "arabic": "ض", "isolated": "ض", "initial": "ضـ", "medial": "ـضـ", "final": "ـض", "joins": True, "order": 15},
    {"name": "To", "arabic": "ط", "isolated": "ط", "initial": "طـ", "medial": "ـطـ", "final": "ـط", "joins": True, "order": 16},
    {"name": "Zo", "arabic": "ظ", "isolated": "ظ", "initial": "ظـ", "medial": "ـظـ", "final": "ـظ", "joins": True, "order": 17},
    {"name": "Ayn", "arabic": "ع", "isolated": "ع", "initial": "عـ", "medial": "ـعـ", "final": "ـع", "joins": True, "order": 18},
    {"name": "Ghayn", "arabic": "غ", "isolated": "غ", "initial": "غـ", "medial": "ـغـ", "final": "ـغ", "joins": True, "order": 19},
    {"name": "Fa", "arabic": "ف", "isolated": "ف", "initial": "فـ", "medial": "ـفـ", "final": "ـف", "joins": True, "order": 20},
    {"name": "Qaf", "arabic": "ق", "isolated": "ق", "initial": "قـ", "medial": "ـقـ", "final": "ـق", "joins": True, "order": 21},
    {"name": "Kaf", "arabic": "ك", "isolated": "ك", "initial": "كـ", "medial": "ـكـ", "final": "ـك", "joins": True, "order": 22},
    {"name": "Lam", "arabic": "ل", "isolated": "ل", "initial": "لـ", "medial": "ـلـ", "final": "ـل", "joins": True, "order": 23},
    {"name": "Meem", "arabic": "م", "isolated": "م", "initial": "مـ", "medial": "ـمـ", "final": "ـم", "joins": True, "order": 24},
    {"name": "Noon", "arabic": "ن", "isolated": "ن", "initial": "نـ", "medial": "ـنـ", "final": "ـن", "joins": True, "order": 25},
    {"name": "He", "arabic": "هـ", "isolated": "ه", "initial": "هـ", "medial": "ـهـ", "final": "ـه", "joins": True, "order": 26},
    {"name": "Waw", "arabic": "و", "isolated": "و", "initial": "و", "medial": "ـو", "final": "ـو", "joins": False, "order": 27},
    {"name": "Ya", "arabic": "ي", "isolated": "ي", "initial": "يـ", "medial": "ـيـ", "final": "ـي", "joins": True, "order": 28},
]

def populate():
    for data in ALPHABET:
        letter, created = Letter.objects.update_or_create(
            name=data["name"],
            defaults={
                "arabic": data["arabic"],
                "isolated": data["isolated"],
                "initial": data["initial"],
                "medial": data["medial"],
                "final": data["final"],
                "joins_to_next": data["joins"],
                "order": data["order"],
            }
        )
        status = "Created" if created else "Updated"
        print(f"{status}: {data['name']}")

if __name__ == "__main__":
    populate()
