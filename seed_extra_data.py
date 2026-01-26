import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from arab.models import ScenarioCategory, Scenario, DialogLine, Word, VocabularyCategory

def seed_more_data():
    # 1. More Scenarios
    cat_life, _ = ScenarioCategory.objects.get_or_create(name="Hayotiy vaziyatlar", icon="fas fa-heartbeat", order=4)
    
    sc_hospital, _ = Scenario.objects.get_or_create(
        category=cat_life,
        title="Shifoxonada",
        description="Shifokorga shikoyatlarni aytish va maslahat olish.",
        difficulty="advanced",
        xp_reward=120
    )

    lines_hospital = [
        ("Shifokor", "مَاذَا تَشْعُرُ اليَوْمَ؟", "Bugun o'zingizni qanday his qilyapsiz?", "Madha tash'uru al-yawma?", 1, False),
        ("Bemor", "تُؤْلِمُنِي رَأْسِي كَثِيراً.", "Boshim juda beryapti.", "Tu'limuni ra'si kathiran.", 2, True),
        ("Shifokor", "هَلْ عِنْدَكَ حُمَّى؟", "Isitrangiz bormi?", "Hal 'indaka humma?", 3, False),
        ("Bemor", "نَعَمْ، حَرَارَتِي مُرْتَفِعَةٌ.", "Ha, haroratim baland.", "Na'am, hararati murtafi'atun.", 4, True),
    ]
    DialogLine.objects.all().filter(scenario=sc_hospital).delete()
    for char, arb, uz, trans, order, is_user in lines_hospital:
        DialogLine.objects.create(
            scenario=sc_hospital, character_name=char, text_arabic=arb, 
            text_uz=uz, transliteration=trans, order=order, is_user_line=is_user
        )

    # 2. More Words with diacritics
    v_cat, _ = VocabularyCategory.objects.get_or_create(name="Kundalik so'zlar")
    words = [
        ("كِتَابٌ", "Kitob", "Kitabun"),
        ("مَدْرَسَةٌ", "Maktab", "Madrasatun"),
        ("طَالِبٌ", "Talaba", "Talibun"),
        ("قَلَمٌ", "Qalam", "Qalamun"),
        ("مَاءٌ", "Suv", "Ma'un"),
        ("خُبْزٌ", "Non", "Khubzun"),
        ("بَيْتٌ", "Uy", "Baytun"),
        ("شَمْسٌ", "Quyosh", "Shamsun"),
    ]
    
    for arb, uz, trans in words:
        Word.objects.get_or_create(
            arabic=arb, 
            translation_uz=uz, 
            transliteration=trans,
            category=v_cat
        )

    print("Additional scenarios and words seeded successfully!")

if __name__ == "__main__":
    seed_more_data()
