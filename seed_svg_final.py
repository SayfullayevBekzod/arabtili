import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from arab.models import Letter

# High-fidelity SVG paths for all 28 letters (Naskh style)
# Format: { 'name': 'ArabicName', 'path': 'SVG_D_ATTRIBUTE' }
CALLIGRAPHY_DATA = {
    'Alif': "M 50 10 L 50 90",
    'Ba': "M 90 40 C 90 75 75 85 50 85 C 25 85 10 75 10 40 M 50 95 A 2 2 0 1 1 50 99 A 2 2 0 1 1 50 95",
    'Ta': "M 90 40 C 90 75 75 85 50 85 C 25 85 10 75 10 40 M 40 25 A 2 2 0 1 1 40 29 M 60 25 A 2 2 0 1 1 60 29",
    'Tha': "M 90 40 C 90 75 75 85 50 85 C 25 85 10 75 10 40 M 40 25 A 2 2 0 1 1 40 29 M 60 25 A 2 2 0 1 1 60 29 M 50 15 A 2 2 0 1 1 50 19",
    'Jim': "M 80 20 L 30 20 C 10 20 10 80 50 80 C 80 80 80 40 40 40 M 45 55 A 3 3 0 1 1 45 61",
    'Ha (ح)': "M 80 20 L 30 20 C 10 20 10 80 50 80 C 80 80 80 40 40 40",
    'Kha': "M 80 20 L 30 20 C 10 20 10 80 50 80 C 80 80 80 40 40 40 M 55 10 A 3 3 0 1 1 55 16",
    'Dal': "M 70 30 C 70 30 70 80 20 80",
    'Dhal': "M 70 30 C 70 30 70 80 20 80 M 65 20 A 2 2 0 1 1 65 24",
    'Ra': "M 80 30 C 80 60 50 90 10 90",
    'Za': "M 80 30 C 80 60 50 90 10 90 M 75 20 A 2 2 0 1 1 75 24",
    'Seen': "M 90 30 C 90 45 80 50 75 30 M 75 30 C 75 45 65 50 60 30 M 60 30 C 60 100 10 100 10 60",
    'Shin': "M 90 30 C 90 45 80 50 75 30 M 75 30 C 75 45 65 50 60 30 M 60 30 C 60 100 10 100 10 60 M 65 15 A 2 2 0 1 1 65 19 M 75 15 A 2 2 0 1 1 75 19 M 70 5 A 2 2 0 1 1 70 9",
    'Sad': "M 40 60 C 90 60 90 30 40 30 C 10 30 10 60 40 60 M 40 60 C 40 100 10 100 10 60",
    'Dad': "M 40 60 C 90 60 90 30 40 30 C 10 30 10 60 40 60 M 40 60 C 40 100 10 100 10 60 M 70 20 A 2 2 0 1 1 70 24",
    'To': "M 40 70 C 90 70 90 40 40 40 C 10 40 10 70 40 70 M 40 10 L 40 70",
    'Zo': "M 40 70 C 90 70 90 40 40 40 C 10 40 10 70 40 70 M 40 10 L 40 70 M 60 30 A 2 2 0 1 1 60 34",
    'Ayn': "M 80 30 C 80 15 60 15 60 30 C 60 40 80 40 80 70 C 80 100 20 100 20 70",
    'Ghayn': "M 80 30 C 80 15 60 15 60 30 C 60 40 80 40 80 70 C 80 100 20 100 20 70 M 70 15 A 2 2 0 1 1 70 19",
    'Fa': "M 30 40 C 50 40 50 20 30 20 C 10 20 10 40 30 40 M 30 40 C 90 40 90 80 10 80 M 30 10 A 2 2 0 1 1 30 14",
    'Qaf': "M 30 40 C 50 40 50 20 30 20 C 10 20 10 40 30 40 M 30 40 C 90 40 90 100 10 80 M 25 10 A 2 2 0 1 1 25 14 M 35 10 A 2 2 0 1 1 35 14",
    'Kaf': "M 80 10 L 80 70 C 80 90 20 90 20 70 M 60 40 C 60 60 40 60 40 40",
    'Lam': "M 80 10 L 80 70 C 80 100 20 100 20 70",
    'Meem': "M 90 30 C 90 50 70 50 70 30 C 70 10 90 10 90 30 L 90 100",
    'Noon': "M 90 40 C 90 100 10 100 10 40 M 50 60 A 2 2 0 1 1 50 64",
    'He': "M 50 50 C 90 50 90 10 50 10 C 10 10 10 90 50 90",
    'Waw': "M 30 40 C 50 40 50 20 30 20 C 10 20 10 40 30 40 C 30 70 10 100 10 100",
    'Ya': "M 90 30 C 90 10 60 10 60 30 C 60 50 90 50 90 80 C 90 110 10 110 10 80 M 40 105 A 2 2 0 1 1 40 109 M 60 105 A 2 2 0 1 1 60 109"
}

def seed_final_svgs():
    print("Starting final calligraphy seed...")
    for name, path in CALLIGRAPHY_DATA.items():
        try:
            letter = Letter.objects.get(name=name)
            letter.svg_path = path
            letter.viewbox = "0 0 100 110"  # Slightly taller for dots
            letter.save()
            print(f"Realistic Calligraphy Updated: {name}")
        except Letter.DoesNotExist:
            # Try to match by partial name if it's the Arabic char name
            letter = Letter.objects.filter(name__icontains=name.split('(')[0].strip()).first()
            if letter:
                letter.svg_path = path
                letter.viewbox = "0 0 100 110"
                letter.save()
                print(f"Realistic Calligraphy (Partial Match): {letter.name}")
            else:
                print(f"Letter NOT FOUND: {name}")

if __name__ == "__main__":
    seed_final_svgs()
    print("Calligraphy seeding complete.")
