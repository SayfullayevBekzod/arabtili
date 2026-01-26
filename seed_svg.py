import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from arab.models import Letter

# Sample SVG paths for Arabic letters (simplified/representative for stroke animation)
LETTER_DATA = {
    'Alif': {
        'arabic': 'ا',
        'svg_path': 'M 50,10 L 50,90',
        'viewbox': '0 0 100 100'
    },
    'Ba': {
        'arabic': 'ب',
        'svg_path': 'M 90,40 C 90,70 10,70 10,40 M 50,85 L 50,85.1', # Curve + dot
        'viewbox': '0 0 100 100'
    },
    'Ta': {
        'arabic': 'ت',
        'svg_path': 'M 90,40 C 90,70 10,70 10,40 M 40,25 L 40,25.1 M 60,25 L 60,25.1',
        'viewbox': '0 0 100 100'
    },
    'Tha': {
        'arabic': 'ث',
        'svg_path': 'M 90,40 C 90,70 10,70 10,40 M 40,25 L 40,25.1 M 60,25 L 60,25.1 M 50,15 L 50,15.1',
        'viewbox': '0 0 100 100'
    },
    'Jim': {
        'arabic': 'ج',
        'svg_path': 'M 30,15 L 80,15 C 80,15 10,15 10,60 C 10,105 100,105 100,60 M 45,65 L 45,65.1',
        'viewbox': '0 0 100 100'
    },
    # Adding more simplified paths for the rest
    'Dal': {'arabic': 'د', 'svg_path': 'M 70,30 C 30,30 30,80 70,80', 'viewbox': '0 0 100 100'},
    'Ra': {'arabic': 'ر', 'svg_path': 'M 60,30 C 60,50 30,90 10,90', 'viewbox': '0 0 100 100'},
    'Seen': {'arabic': 'س', 'svg_path': 'M 90,30 C 90,60 75,60 75,30 C 75,60 60,60 60,30 C 60,80 10,80 10,40', 'viewbox': '0 0 100 100'},
    'Lam': {'arabic': 'ل', 'svg_path': 'M 70,10 L 70,70 C 70,100 10,100 10,70', 'viewbox': '0 0 100 100'},
    'Meem': {'arabic': 'م', 'svg_path': 'M 80,40 C 80,60 50,60 50,40 C 50,20 80,20 80,40 L 50,40 L 50,90', 'viewbox': '0 0 100 100'},
    'Noon': {'arabic': 'ن', 'svg_path': 'M 90,40 C 90,90 10,90 10,40 M 50,25 L 50,25.1', 'viewbox': '0 0 100 100'},
    'Wov': {'arabic': 'و', 'svg_path': 'M 60,40 C 60,60 80,60 80,40 C 80,20 60,20 60,40 C 60,60 30,90 10,90', 'viewbox': '0 0 100 100'},
    'Ya': {'arabic': 'ي', 'svg_path': 'M 90,30 C 90,50 60,50 60,30 C 60,10 30,10 30,40 C 30,90 100,90 100,50', 'viewbox': '0 0 100 100'},
}

def seed_svg():
    letters = Letter.objects.all()
    count = 0
    for letter in letters:
        name = letter.name
        if name in LETTER_DATA:
            letter.svg_path = LETTER_DATA[name]['svg_path']
            letter.viewbox = LETTER_DATA[name]['viewbox']
            letter.save()
            count += 1
            print(f"Updated {name}")
        else:
            # Provide generic fallback if path not specifically defined
            # (In real app, we'd have all 28)
            if not letter.svg_path:
                letter.svg_path = "M 20,50 L 80,50" # placeholder line
                letter.save()
                print(f"Placeholder for {name}")

    print(f"SVG seeding complete. Updated {count} letters specifically.")

if __name__ == "__main__":
    seed_svg()
