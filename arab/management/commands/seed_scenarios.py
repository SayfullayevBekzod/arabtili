from django.core.management.base import BaseCommand
from arab.models import ScenarioCategory, Scenario, DialogLine, PhrasebookEntry

class Command(BaseCommand):
    help = 'Seed conversational scenarios and phrasebook'

    def handle(self, *args, **options):
        # 1. Categories
        cat_daily, _ = ScenarioCategory.objects.get_or_create(name="Kundalik muloqot", defaults={'icon': "fas fa-home", 'order': 1})
        cat_travel, _ = ScenarioCategory.objects.get_or_create(name="Sayohat", defaults={'icon': "fas fa-plane", 'order': 2})
        cat_shop, _ = ScenarioCategory.objects.get_or_create(name="Bozor va Xarid", defaults={'icon': "fas fa-shopping-bag", 'order': 3})
        cat_life, _ = ScenarioCategory.objects.get_or_create(name="Hayotiy vaziyatlar", defaults={'icon': "fas fa-heartbeat", 'order': 4})

        # 2. Scenarios
        sc_airport, _ = Scenario.objects.get_or_create(
            category=cat_travel,
            title="Aeroportda",
            defaults={
                'description': "Parvozga ro'yxatdan o'tish va darvozani topish.",
                'difficulty': "intermediate",
                'xp_reward': 100
            }
        )

        sc_dinner, _ = Scenario.objects.get_or_create(
            category=cat_daily,
            title="Restoranda",
            defaults={
                'description': "Ovqat buyurtma qilish va hisobni so'rash.",
                'difficulty': "beginner",
                'xp_reward': 80
            }
        )

        # 3. Dialog Lines for Airport
        DialogLine.objects.filter(scenario=sc_airport).delete()
        lines_airport = [
            ("Xodim", "أَيْنَ تَذْهَبُ اليَوْمَ؟", "Bugun qayerga ketyapsiz?", "Ayna tadh-habu al-yawma?", 1, False),
            ("Sayohatichi", "أَنَا ذَاهِبٌ إِلَى مَكَّةَ.", "Makkaga ketyapman.", "Ana dhahibun ila Makkata.", 2, True),
            ("Xodim", "هَلْ مَعَكَ جَوَازُ السَّفَرِ؟", "Sizda passportingiz bormi?", "Hal ma'aka jawazu as-safari?", 3, False),
            ("Sayohatichi", "نَعَمْ، تَفَضَّلْ. هَذَا هُوَ الجَوَازُ.", "Ha, marhamat. Mana passport.", "Na'am, tafaddal. Hadha huwa al-jawazu.", 4, True),
        ]
        for char, arb, uz, trans, order, is_user in lines_airport:
            DialogLine.objects.create(
                scenario=sc_airport, character_name=char, text_arabic=arb, 
                text_uz=uz, transliteration=trans, order=order, is_user_line=is_user
            )

        # 4. Dialog Lines for Dinner
        DialogLine.objects.filter(scenario=sc_dinner).delete()
        lines_dinner = [
            ("Ofitsiant", "مَاذَا تُرِيدُ أَنْ تَأْكُلَ؟", "Nima yeyishni xohlaysiz?", "Madha turidu an ta'kula?", 1, False),
            ("Mijoz", "أُرِيدُ دَجَاجاً مَشْوِيّاً مَعَ الأَرُزِّ.", "Guruch bilan qovurilgan tovuq xohlayman.", "Uridu dajajan mashwiyyan ma'a al-aruzzi.", 2, True),
            ("Ofitsiant", "وَهَلْ تُرِيدُ شَيْئاً لِلشُّرْبِ؟", "Ichishga-chi, biror nima xohlaysizmi?", "Wa hal turidu shay'an lish-shurbi?", 3, False),
            ("Mijoz", "عَصِيرَ بُرْتُقَالٍ بَارِداً، مِنْ فَضْلِكَ.", "Iltimos, sovuq apelsin sharbati.", "Asira burtuqalin baridan, min fadlika.", 4, True),
        ]
        for char, arb, uz, trans, order, is_user in lines_dinner:
            DialogLine.objects.create(
                scenario=sc_dinner, character_name=char, text_arabic=arb, 
                text_uz=uz, transliteration=trans, order=order, is_user_line=is_user
            )

        # 5. Phrasebook Entries
        phrases = [
            (cat_daily, "أَهْلًا وَسَهْلًا", "Xush kelibsiz", "Ahlan wa sahlan"),
            (cat_daily, "كَيْفَ حَالُكَ؟", "Ahvolingiz qanday?", "Kayfa haluka?"),
            (cat_daily, "أَنَا بِخَيْرٍ، شُكْراً", "Men yaxshiman, rahmat", "Ana bikhayrin, shukran"),
            (cat_shop, "بِكَمْ هَذَا الكِتَابُ؟", "Bu kitob necha pul?", "Bikam hadha al-kitabu?"),
            (cat_shop, "هَلْ هُنَاكَ خَصْمٌ؟", "Chegirma bormi?", "Hal hunaka khasmun?"),
            (cat_travel, "أَيْنَ المَحَطَّةُ؟", "Bekat qayerda?", "Ayna al-mahattatu?"),
            (cat_travel, "أُرِيدُ تِذْكِرَةً وَاحِدَةً.", "Bitta chipta xohlayman.", "Uridu tidhkiratan wahidatan."),
        ]
        PhrasebookEntry.objects.all().delete()
        for cat, arb, uz, trans in phrases:
            PhrasebookEntry.objects.create(category=cat, text_arabic=arb, text_uz=uz, transliteration=trans)

        self.stdout.write(self.style.SUCCESS("Enhanced conversational data seeded successfully!"))
