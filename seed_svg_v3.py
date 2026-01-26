import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from arab.models import Letter

# More realistic "Calligraphy" paths (multiple strokes where needed)
# For simplicity in this demo, we use single paths that are more "curvy" and calligraphy-like
LETTER_DATA_V3 = {
    'Alif': {
        'arabic': 'ا',
        'svg_path': 'M 50,15 L 50,85',
        'viewbox': '0 0 100 100'
    },
    'Ba': {
        'arabic': 'ب',
        'svg_path': 'M 90,45 C 90,75 10,75 10,45 M 50,85 L 50,85.1', # Dot is separate
        'viewbox': '0 0 100 100'
    },
    'Jim': {
        'arabic': 'ج',
        'svg_path': 'M 30,20 L 80,20 C 80,20 10,20 10,60 C 10,105 100,105 100,60 M 45,65 L 45,65.1',
        'viewbox': '0 0 100 100'
    },
    'Seen': {
        'arabic': 'س',
        'svg_path': 'M 90,35 C 90,65 75,65 75,35 C 75,65 60,65 60,35 C 60,85 10,85 10,45',
        'viewbox': '0 0 100 100'
    },
    'Ayn': {
        'arabic': 'ع',
        'svg_path': 'M 80,30 C 80,10 40,10 40,30 C 40,50 80,50 80,70 C 80,100 10,100 10,70',
        'viewbox': '0 0 100 100'
    },
    'Lam': {
        'arabic': 'ل',
        'svg_path': 'M 70,15 L 70,75 C 70,105 10,105 10,75',
        'viewbox': '0 0 100 100'
    },
    'Meem': {
        'arabic': 'م',
        'svg_path': 'M 85,45 C 85,65 55,65 55,45 C 55,25 85,25 85,45 L 55,45 L 55,95',
        'viewbox': '0 0 100 100'
    },
    'Wov': {
        'arabic': 'و',
        'svg_path': 'M 65,45 C 65,65 85,65 85,45 C 85,25 65,25 65,45 C 65,65 35,95 15,95',
        'viewbox': '0 0 100 100'
    }
}

def seed_svg_v3():
    letters = Letter.objects.all()
    count = 0
    for letter in letters:
        name = letter.name
        if name in LETTER_DATA_V3:
            letter.svg_path = LETTER_DATA_V3[name]['svg_path']
            letter.viewbox = LETTER_DATA_V3[name]['viewbox']
            letter.save()
            count += 1
            print(f"Realistic Calligraphy: {name}")
        else:
            # Fallback for others if missing
            if not letter.svg_path or letter.svg_path == "M 20,50 L 80,50":
                # Generate a slightly better generic curve
                letter.svg_path = "M 80,40 C 80,80 20,80 20,40"
                letter.save()
                print(f"Generic Curve: {name}")

    print(f"SVG v3 seeding complete. {count} realistic letters updated.")

if __name__ == "__main__":
    seed_svg_v3()
