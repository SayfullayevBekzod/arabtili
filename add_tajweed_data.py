import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from arab.models import TajweedRule, TajweedExample

def add_data():
    examples_data = [
        # Idgham
        ("Idgham (Birlashuv)", "مِمَّن يَقُولُ", "A1"),
        ("Idgham (Birlashuv)", "مِن وَالٍ", "A1"),
        ("Idgham (Birlashuv)", "مِن نُّورٍ", "A1"),
        
        # Ikhfa
        ("Ikhfa (Yashirish)", "أَن جَاءَكَ", "A1"),
        ("Ikhfa (Yashirish)", "مِن دُونِ", "A1"),
        ("Ikhfa (Yashirish)", "وَمَن ضَلَّ", "A1"),
        
        # Izhor
        ("Izhor (Aniq o'qish)", "مِنْ حَيْثُ", "A1"),
        ("Izhor (Aniq o'qish)", "أَنْعَمْتَ", "A1"),
        ("Izhor (Aniq o'qish)", "مِنْ غَيْرِ", "A1"),
        
        # Qalqalah
        ("Qalqalah (Tebratish)", "بِالْحَقِّ", "A1"),
        ("Qalqalah (Tebratish)", "طَبَقٍ", "A1"),
        ("Qalqalah (Tebratish)", "أَبْصَارِهِمْ", "A1"),
    ]
    
    for rule_title, text, level in examples_data:
        rule = TajweedRule.objects.filter(title__icontains=rule_title).first()
        if rule:
            TajweedExample.objects.get_or_create(
                rule=rule,
                arabic_text=text
            )
            print(f"Added: {text} for {rule.title}")
        else:
            print(f"Rule not found: {rule_title}")

if __name__ == "__main__":
    add_data()
