import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from arab.models import Letter

l = Letter.objects.filter(arabic='ا').first()
if l:
    l.svg_path = 'M50,15 L50,85'
    l.viewbox = '0 0 100 100'
    l.save()
    print(f'SUCCESS: Updated {l.name}')
else:
    print('ERROR: Alif letter not found')
