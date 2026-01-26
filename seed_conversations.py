import os
import django
import sys

sys.path.append(r"d:\Work\arab")
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from arab.models import ScenarioCategory, Scenario, DialogLine, PhrasebookEntry

def seed_scenarios():
    print("Seeding scenarios...")
    
    # 1. Categories
    cat_daily, _ = ScenarioCategory.objects.get_or_create(
        name="Daily Life",
        defaults={"icon": "fas fa-coffee", "description": "Everyday situations", "order": 1}
    )
    cat_travel, _ = ScenarioCategory.objects.get_or_create(
        name="Travel",
        defaults={"icon": "fas fa-plane", "description": "Airport, Hotel, Taxi", "order": 2}
    )
    
    # 2. Scenario 1: Greeting a Friend
    s1, _ = Scenario.objects.get_or_create(
        title="Meeting a New Friend",
        category=cat_daily,
        defaults={
            "description": "Learn how to introduce yourself politely.",
            "difficulty": "beginner",
            "xp_reward": 50,
            "order": 1
        }
    )
    
    # Lines for S1
    lines_s1 = [
        ("Ahmad", "السَّلَامُ عَلَيْكُمْ", "Assalamu alaykum", "Assalomu alaykum", False),
        ("User", "وَعَلَيْكُمُ السَّلَامُ", "Wa alaykumus salam", "Va alaykum assalom", True),
        ("Ahmad", "كَيْفَ حَالُكَ؟", "Kayfa haluka?", "Ahvolingiz qanday?", False),
        ("User", "بِخَيْرٍ، وَالحَمْدُ لِلَّهِ. وَأَنْتَ؟", "Bi-khayr, wal-hamdu lillah. Wa anta?", "Yaxshi, Alhamdulillah. O'zingizchi?", True),
        ("Ahmad", "أَنَا بِخَيْرٍ أَيْضًا. مَا اسْمُكَ؟", "Ana bi-khayr ayzan. Ma ismuka?", "Men ham yaxshiman. Ismingiz nima?", False),
        ("User", "اِسْمِي (ozingizni ismingizni ayting)", "Ismi ...", "Mening ismim ...", True),
    ]
    
    DialogLine.objects.filter(scenario=s1).delete()
    for i, (char, arab, trans, uz, is_user) in enumerate(lines_s1):
        DialogLine.objects.create(
            scenario=s1,
            character_name=char,
            text_arabic=arab,
            transliteration=trans,
            text_uz=uz,
            order=i+1,
            is_user_line=is_user
        )
        
    # 3. Scenario 2: At the Market
    s2, _ = Scenario.objects.get_or_create(
        title="At the Market",
        category=cat_daily,
        defaults={
            "description": "Buying fruits and vegetables.",
            "difficulty": "beginner",
            "xp_reward": 70,
            "order": 2
        }
    )
    
    lines_s2 = [
        ("Seller", "أَهْلًا وَسَهْلًا! مَاذَا تُرِيدُ؟", "Ahlan wa sahlan! Madha turid?", "Xush kelibsiz! Nima xohlaysiz?", False),
        ("User", "أُرِيدُ بَعْضَ التُّفَّاحِ، مِنْ فَضْلِكَ.", "Uridu ba'da at-tuffah, min fadlik.", "Biroz olma xohlayman, iltimos.", True),
        ("Seller", "بِكَمِ الْكِيلُو؟", "Bikam al-kilo?", "Kiloyiga qancha?", False),
        ("User", "الْكِيلُو بِخَمْسَةِ دَنَانِيرَ.", "Al-kilo bi-khamsati dananir.", "Kiloyi 5 dinor.", True), # Mistake in logic? Usually seller says price. Fixed below.
    ] 
    
    # Correction: User asks price, Seller answers.
    lines_s2_corrected = [
        ("Seller", "أَهْلًا وَسَهْلًا! مَاذَا تُرِيدُ؟", "Ahlan wa sahlan! Madha turid?", "Xush kelibsiz! Nima xohlaysiz?", False),
        ("User", "أُرِيدُ بَعْضَ التُّفَّاحِ، مِنْ فَضْلِكَ.", "Uridu ba'da at-tuffah, min fadlik.", "Biroz olma xohlayman, iltimos.", True),
        ("User", "بِكَمِ الْكِيلُو؟", "Bikam al-kilo?", "Bir kilosi qancha?", True),
        ("Seller", "الْكِيلُو بِخَمْسَةِ دَنَانِيرَ.", "Al-kilo bi-khamsati dananir.", "Bir kilosi 5 dinor.", False),
        ("User", "هَذَا جَيِّدٌ. أَعْطِنِي كِيلُو وَاحِدًا.", "Hadha jayyid. A'tini kilo wahidan.", "Yaxshi. Menga bir kilo bering.", True),
    ]

    DialogLine.objects.filter(scenario=s2).delete()
    for i, (char, arab, trans, uz, is_user) in enumerate(lines_s2_corrected):
        DialogLine.objects.create(
            scenario=s2,
            character_name=char,
            text_arabic=arab,
            transliteration=trans,
            text_uz=uz,
            order=i+1,
            is_user_line=is_user
        )

    # 4. Phrasebook - Greetings
    phrases = [
        ("مَرْحَبًا", "Marhaban", "Salom"),
        ("صَبَاحَ الْخَيْرِ", "Sabahal khayr", "Xayrli tong"),
        ("مَسَاءَ الْخَيْرِ", "Masa'al khayr", "Xayrli kech"),
        ("تُصْبِحُ عَلَى خَيْرٍ", "Tusbihu 'ala khayr", "Xayrli tun"),
    ]
    
    for arab, trans, uz in phrases:
        PhrasebookEntry.objects.get_or_create(
            category=cat_daily,
            text_arabic=arab,
            defaults={"transliteration": trans, "text_uz": uz}
        )
        
    print("Seeding scenarios complete.")

if __name__ == "__main__":
    seed_scenarios()
