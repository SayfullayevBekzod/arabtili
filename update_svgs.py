
# Authentic Arabic Calligraphy SVG Paths (Thuluth/Naskh Style)
# Coordinate system: 0-100 viewbox.
# Designed for stroke animation: Separate disconnected parts with different paths or M moves.

ARABIC_SVGS = {
    # 1. Alif (ا): Vertical stroke, slightly tapered
    'Alif': "M50,15 C50,15 50,40 50,60 C50,75 52,80 48,85",
    
    # 2. Ba (ب): Shallow boat, dot below center
    'Ba': "M85,55 Q50,55 15,55 Q10,55 10,45 M50,80 q0,5 0,5",
    
    # 3. Ta (ت): Shallow boat, two dots above center
    'Ta': "M85,55 Q50,55 15,55 Q10,55 10,45 M35,30 q0,5 0,5 M65,30 q0,5 0,5",
    
    # 4. Tha (ث): Shallow boat, three dots pyramid
    'Tha': "M85,55 Q50,55 15,55 Q10,55 10,45 M35,30 q0,5 0,5 M65,30 q0,5 0,5 M50,15 q0,5 0,5",
    
    # 5. Jim (ج): Wave top, big C body, dot inside
    'Jim': "M30,35 Q50,35 60,35 L90,35 Q70,55 50,65 Q30,85 70,95 M50,70 q0,5 0,5",
    
    # 6. Ha (ح): Wave top, big C body, no dot
    'Ha': "M30,35 Q50,35 60,35 L90,35 Q70,55 50,65 Q30,85 70,95",
    
    # 7. Kha (خ): Wave top, big C body, dot above
    'Kha': "M30,35 Q50,35 60,35 L90,35 Q70,55 50,65 Q30,85 70,95 M50,15 q0,5 0,5",
    
    # 8. Dal (د): Acute angle < shape
    'Dal': "M55,35 Q70,35 70,50 Q70,70 35,70",
    
    # 9. Dhal (ذ): Acute angle, dot above
    'Dhal': "M55,35 Q70,35 70,50 Q70,70 35,70 M55,20 q0,5 0,5",
    
    # 10. Ra (ر): Banana shape falling below line
    'Ra': "M60,35 Q60,55 30,80",
    
    # 11. Zay (ز): Banana shape, dot above
    'Zay': "M60,35 Q60,55 30,80 M55,20 q0,5 0,5",
    
    # 12. Sin (س): 3 teeth, big bowl
    'Sin': "M90,45 Q85,45 80,45 Q75,45 70,45 Q65,45 60,45 M60,45 Q60,85 20,75",
    
    # 13. Shin (ش): 3 teeth, big bowl, 3 dots
    'Shin': "M90,45 Q85,45 80,45 Q75,45 70,45 Q65,45 60,45 M60,45 Q60,85 20,75 M75,25 q0,5 0,5 M65,25 q0,5 0,5 M85,25 q0,5 0,5",
    
    # 14. Sad (ص): Loop head, tooth, big bowl
    'Sad': "M35,45 Q45,25 75,25 Q95,25 85,45 Q75,45 35,45 M35,45 L30,45 Q30,85 10,75",
    
    # 15. Dad (ض): Sad + dot
    'Dad': "M35,45 Q45,25 75,25 Q95,25 85,45 Q75,45 35,45 M35,45 L30,45 Q30,85 10,75 M55,15 q0,5 0,5",
    
    # 16. Ta (ط): Loop head, vertical alif
    'Ta (hard)': "M35,60 Q45,40 75,40 Q95,40 85,60 Q75,60 35,60 M65,15 L65,60",
    
    # 17. Za (ظ): Ta + dot
    'Zo': "M35,60 Q45,40 75,40 Q95,40 85,60 Q75,60 35,60 M65,15 L65,60 M65,25 q0,5 0,5",
    
    # 18. Ayn (ع): Small C top, Big C bottom
    'Ayn': "M65,30 Q40,30 40,50 Q40,60 65,60 Q90,90 35,90",
    
    # 19. Ghayn (غ): Ayn + dot
    'Ghayn': "M65,30 Q40,30 40,50 Q40,60 65,60 Q90,90 35,90 M60,15 q0,5 0,5",
    
    # 20. Fa (ف): Loop head, flat body, dot
    'Fa': "M75,35 Q85,25 90,35 Q95,45 85,45 Q75,45 75,35 M75,45 Q60,45 20,45 Q10,45 10,35 M80,15 q0,5 0,5",
    
    # 21. Qaf (ق): Loop head, deep bowl, 2 dots
    'Qaf': "M75,35 Q85,25 90,35 Q95,45 85,45 Q75,45 75,35 M75,45 Q65,85 35,80 M75,15 q0,5 0,5 M85,15 q0,5 0,5",
    
    # 22. Kaf (ك): Top stroke, vertical, bottom horizontal, hamza
    'Kaf': "M75,15 L75,65 Q50,65 20,65 M50,40 L45,45 L50,50", 
    
    # 23. Lam (ل): Vertical, deep bowl hook
    'Lam': "M70,10 L70,60 Q70,90 35,80",
    
    # 24. Mim (م): Loop head, tail down
    'Meem': "M65,50 Q55,60 45,50 Q55,40 65,50 M45,50 L45,90",
    
    # 25. Nun (ن): Deep bowl, dot inside/above
    'Noon': "M85,35 Q60,85 20,35 M52,25 q0,5 0,5",
    
    # 26. Ha (هـ): D shape + loop inside
    'He': "M75,30 Q75,70 50,70 L40,50 Q45,25 75,30 M50,70 L25,70", 
    
    # 27. Waw (و): Loop head, Ra tail
    'Waw': "M60,40 Q70,30 80,40 Q85,50 75,50 Q65,50 60,40 M60,50 Q60,80 30,85",
    
    # 28. Ya (ي): Swan neck, big bowl, 2 dots
    'Ya': "M75,30 Q60,50 50,40 Q40,30 30,40 Q25,50 45,85 M40,95 q0,5 0,5 M50,95 q0,5 0,5"
}

import os
import django
import sys

sys.path.append(r"d:\Work\arab")
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from arab.models import Letter

def update_letters():
    count = 0
    # Direct mapping for tricky names
    special_map = {
        'Ha (ح)': ARABIC_SVGS['Ha'],
        'He': ARABIC_SVGS['He'],
        'Meem': ARABIC_SVGS['Meem'],
        'Noon': ARABIC_SVGS['Noon'],
        'Seen': ARABIC_SVGS['Sin'],
        'To': ARABIC_SVGS['Ta (hard)'],
        'Zo': ARABIC_SVGS['Zo'],
    }

    for name, svg in ARABIC_SVGS.items():
        # First try the special map
        for db_name, special_svg in special_map.items():
             if name == db_name: # handled above
                  continue
        
        # Try to find letter by name (fuzzy match)
        letters = Letter.objects.filter(name__icontains=name)
        
        # Also try direct DB name lookups from special_map
        for key in special_map:
             l_spec = Letter.objects.filter(name=key)
             for l in l_spec:
                  l.svg_path = special_map[key]
                  l.save()
                  print(f"Updated {l.name} with authentic SVG (Special Map).")

        for l in letters:
            # Skip if already updated via special map
            if l.name in special_map: continue
            
            # Simple fuzzy Match
            if name.lower() in l.name.lower() or (name == 'Ba' and 'Be' in l.name) or (name == 'Tha' and 'Te' in l.name): 
                 l.svg_path = svg
                 l.save()
                 print(f"Updated {l.name} with authentic SVG.")
                 count += 1
    
    print(f"Updated {count} letters.")

if __name__ == "__main__":
    update_letters()
