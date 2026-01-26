import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from arab.models import Scenario, DialogLine, PhrasebookEntry, Letter

def vocalize_everything():
    # 1. Update Tanishuv Scenario (Ahmad & Sami)
    sc_intro = Scenario.objects.filter(title__icontains="Tanishuv").first()
    if sc_intro:
        lines = DialogLine.objects.filter(scenario=sc_intro).order_by('order')
        vocalized_lines = [
            ("السَّلَامُ عَلَيْكُمْ وَرَحْمَةُ اللهِ وَبَرَكَاتُهُ", "Assalomu alaykum va rohmatullohi va barokatuh"),
            ("وَعَلَيْكُمُ السَّلَامُ وَرَحْمَةُ اللهِ وَبَرَكَاتُهُ. أَهْلًا وَسَهْلًا", "Va alaykum assalom va rohmatullohi va barokatuh. Xush kelibsiz!"),
            ("كَيْفَ حَالُكَ؟ مَا اسْمُكَ؟", "Ahvolingiz qanday? Ismingiz nima?"),
            ("أَنَا بِخَيْرٍ، وَأَنْتَ؟ اسْمِي سَامِي.", "Men yaxshiman, o'zingiz-chi? Ismim Sami."),
            ("اسْمِي أَحْمَدُ. تَشَرَّفْنَا!", "Ismim Ahmad. Tanishganimdan xursandman!"),
            ("تَشَرَّفْنَا أَيْضًا. إِلَى اللِّقَاءِ!", "Biz ham xursandmiz. Ko'rishguncha!"),
            ("مَعَ السَّلَامَةِ!", "Xayr, salomat bo'ling!"),
        ]
        for i, (arb, uz) in enumerate(vocalized_lines):
            line = lines.filter(order=i+1).first()
            if line:
                line.text_arabic = arb
                line.save()
        print("Intro Scenario vocalized.")

    # 2. Update Phrasebook
    phrases = PhrasebookEntry.objects.all()
    vocalized_phrases = {
        "أهلاً وسهلاً": "أَهْلًا وَسَهْلًا",
        "كيف حالك؟": "كَيْفَ حَالُكَ؟",
        "أنا بخير، شكراً": "أَنَا بِخَيْرٍ، شُكْراً",
        "السلام عليكم": "السَّلَامُ عَلَيْكُمْ",
        "وعليكم السلام": "وَعَلَيْكُمُ السَّلَامُ",
        "إلى اللقاء": "إِلَى اللِّقَاءِ",
        "مع السلامة": "مَعَ السَّلَامَةِ",
    }
    for p in phrases:
        if p.text_arabic in vocalized_phrases:
            p.text_arabic = vocalized_phrases[p.text_arabic]
            p.save()
    print("Phrasebook vocalized.")

    # 3. Fix Dhal Calligraphy and Order
    dhal = Letter.objects.filter(name="Dhal").first()
    if dhal:
        # A more 'realistic' Dhal path (two segments: top curve and bottom horizontal base)
        dhal.svg_path = "M 70,30 C 70,30 30,30 30,60 L 75,60 M 55,20 L 55,20.1" # Added dot for Dhal
        dhal.save()
        print("Dhal calligraphy updated.")

    print("Vocalize All task complete!")

if __name__ == "__main__":
    vocalize_everything()
