from django.core.management.base import BaseCommand
from arab.models import VocabularyCategory, Word, Diacritic

class Command(BaseCommand):
    help = 'Seeds the dictionary with high-quality Arabic words across common categories.'

    def handle(self, *args, **options):
        # Categories to seed
        categories_data = [
            {"name": "Oila (Family)", "desc": "Oilaga oid eng ko'p qo'llaniladigan so'zlar"},
            {"name": "Maktab (School)", "desc": "O'qish va maktab hayotiga oid so'zlar"},
            {"name": "Uy (Home)", "desc": "Uy buyumlari va xonalar"},
            {"name": "Ovqat (Food)", "desc": "Mevalar, ovqatlar va ichimliklar"},
            {"name": "Hayvonlar (Animals)", "desc": "Uy va yovvoyi hayvonlar"},
            {"name": "Ranglar (Colors)", "desc": "Asosiy ranglar"},
            {"name": "Raqamlar (Numbers)", "desc": "1 dan 10 gacha bo'lgan raqamlar"},
            {"name": "Salomlashish (Greetings)", "desc": "Kundalik muloqot iboralari"},
            {"name": "Sifatlar (Adjectives)", "desc": "Sifat va xususiyat so'zlari"},
        ]

        # Seed categories
        categories = {}
        for cat in categories_data:
            obj, created = VocabularyCategory.objects.get_or_create(
                name=cat["name"],
                defaults={"description": cat["desc"]}
            )
            categories[cat["name"]] = obj
            if created:
                self.stdout.write(self.style.SUCCESS(f"Category '{cat['name']}' created."))

        # Words data
        words_data = [
            # Family
            {"arabic": "أَبٌ", "trans": "Abun", "uz": "Ota", "cat": "Oila (Family)"},
            {"arabic": "أُمٌّ", "trans": "Ummun", "uz": "Ona", "cat": "Oila (Family)"},
            {"arabic": "أَخٌ", "trans": "Akhun", "uz": "Aka/Uka", "cat": "Oila (Family)"},
            {"arabic": "أُخْتٌ", "trans": "Ukhtun", "uz": "Opa/Singil", "cat": "Oila (Family)"},
            {"arabic": "جَدٌّ", "trans": "Jaddun", "uz": "Boba", "cat": "Oila (Family)"},
            {"arabic": "جَدَّةٌ", "trans": "Jaddatun", "uz": "Bibi", "cat": "Oila (Family)"},
            
            # School
            {"arabic": "مَدْرَسَةٌ", "trans": "Madrasatun", "uz": "Maktab", "cat": "Maktab (School)"},
            {"arabic": "طَالِبٌ", "trans": "Talibun", "uz": "O'quvchi (m)", "cat": "Maktab (School)"},
            {"arabic": "أُسْتَاذٌ", "trans": "Ustadhun", "uz": "Ustoz", "cat": "Maktab (School)"},
            {"arabic": "سَبُّورَةٌ", "trans": "Sabburatun", "uz": "Doska", "cat": "Maktab (School)"},
            {"arabic": "حَقِيبَةٌ", "trans": "Haqibatun", "uz": "Sumka", "cat": "Maktab (School)"},
            
            # Home
            {"arabic": "بَيْتٌ", "trans": "Baytun", "uz": "Uy", "cat": "Uy (Home)"},
            {"arabic": "بَابٌ", "trans": "Babun", "uz": "Eshik", "cat": "Uy (Home)"},
            {"arabic": "نَافِذَةٌ", "trans": "Nafidhatun", "uz": "Deraza", "cat": "Uy (Home)"},
            {"arabic": "سَرِيرٌ", "trans": "Sarirun", "uz": "Karavot", "cat": "Uy (Home)"},
            {"arabic": "طَاوِلَةٌ", "trans": "Tawilatun", "uz": "Stol", "cat": "Uy (Home)"},
            {"arabic": "كُرْسِيٌّ", "trans": "Kursiyyun", "uz": "Stul", "cat": "Uy (Home)"},
            
            # Food
            {"arabic": "تُفَّاحٌ", "trans": "Tuffahun", "uz": "Olma", "cat": "Ovqat (Food)"},
            {"arabic": "مَوْزٌ", "trans": "Mawzun", "uz": "Banan", "cat": "Ovqat (Food)"},
            {"arabic": "عِنَبٌ", "trans": "Inabun", "uz": "Uzum", "cat": "Ovqat (Food)"},
            {"arabic": "خُبْزٌ", "trans": "Khubzun", "uz": "Non", "cat": "Ovqat (Food)"},
            {"arabic": "حَلِيبٌ", "trans": "Halibun", "uz": "Sut", "cat": "Ovqat (Food)"},
            {"arabic": "مَاءٌ", "trans": "Ma'un", "uz": "Suv", "cat": "Ovqat (Food)"},
            
            # Animals
            {"arabic": "أَسَدٌ", "trans": "Asadun", "uz": "Sher", "cat": "Hayvonlar (Animals)"},
            {"arabic": "جَمَلٌ", "trans": "Jamalun", "uz": "Tuya", "cat": "Hayvonlar (Animals)"},
            {"arabic": "فِيلٌ", "trans": "Filun", "uz": "Fil", "cat": "Hayvonlar (Animals)"},
            {"arabic": "قِطٌّ", "trans": "Qittun", "uz": "Mushuk", "cat": "Hayvonlar (Animals)"},
            {"arabic": "كَلْبٌ", "trans": "Kalbun", "uz": "Kuchuk", "cat": "Hayvonlar (Animals)"},
            
            # Colors
            {"arabic": "أَبْيَضُ", "trans": "Abyad", "uz": "Oq", "cat": "Ranglar (Colors)"},
            {"arabic": "أَسْوَدُ", "trans": "Aswad", "uz": "Qora", "cat": "Ranglar (Colors)"},
            {"arabic": "أَحْمَرُ", "trans": "Ahmar", "uz": "Qizil", "cat": "Ranglar (Colors)"},
            {"arabic": "أَزْرَقُ", "trans": "Azraq", "uz": "Ko'k", "cat": "Ranglar (Colors)"},
            {"arabic": "أَخْضَرُ", "trans": "Akhdar", "uz": "Yashil", "cat": "Ranglar (Colors)"},
            
            # Numbers
            {"arabic": "وَاحِدٌ", "trans": "Wahid", "uz": "Bir", "cat": "Raqamlar (Numbers)"},
            {"arabic": "اِثْنَانِ", "trans": "Ithnan", "uz": "Ikki", "cat": "Raqamlar (Numbers)"},
            {"arabic": "ثَلَاثَةٌ", "trans": "Thalathah", "uz": "Uch", "cat": "Raqamlar (Numbers)"},
            {"arabic": "أَرْبَعَةٌ", "trans": "Arba'ah", "uz": "To'rt", "cat": "Raqamlar (Numbers)"},
            {"arabic": "خَمْسَةٌ", "trans": "Khamsah", "uz": "Besh", "cat": "Raqamlar (Numbers)"},
            
            # Greetings & Basic
            {"arabic": "صَبَاحُ الْخَيْرِ", "trans": "Sabahul khayr", "uz": "Xayrli tong", "cat": "Salomlashish (Greetings)"},
            {"arabic": "مَسَاءُ الْخَيْرِ", "trans": "Masa'ul khayr", "uz": "Xayrli kech", "cat": "Salomlashish (Greetings)"},
            {"arabic": "شُكْرًا", "trans": "Shukran", "uz": "Rahmat", "cat": "Salomlashish (Greetings)"},
            {"arabic": "عَفْوًا", "trans": "Afwan", "uz": "Arzimaydi", "cat": "Salomlashish (Greetings)"},
            {"arabic": "إِلَى اللِّقَاءِ", "trans": "Ilal liqo", "uz": "Ko'rishguncha", "cat": "Salomlashish (Greetings)"},
            
            # Adjectives
            {"arabic": "كَبِيرٌ", "trans": "Kabir", "uz": "Katta", "cat": "Sifatlar (Adjectives)"},
            {"arabic": "صَغِيرٌ", "trans": "Saghir", "uz": "Kichik", "cat": "Sifatlar (Adjectives)"},
            {"arabic": "جَمِيلٌ", "trans": "Jamil", "uz": "Chiroyli", "cat": "Sifatlar (Adjectives)"},
            {"arabic": "بَعِيدٌ", "trans": "Ba'id", "uz": "Uzoq", "cat": "Sifatlar (Adjectives)"},
            {"arabic": "قَرِيبٌ", "trans": "Qarib", "uz": "Yaqin", "cat": "Sifatlar (Adjectives)"},
            {"arabic": "جَدِيدٌ", "trans": "Jadid", "uz": "Yangi", "cat": "Sifatlar (Adjectives)"},
            {"arabic": "قَدِيمٌ", "trans": "Qadim", "uz": "Eski", "cat": "Sifatlar (Adjectives)"},
        ]

        # Seed words
        total_created = 0
        for w in words_data:
            word_obj, created = Word.objects.get_or_create(
                arabic=w["arabic"],
                defaults={
                    "transliteration": w["trans"],
                    "translation_uz": w["uz"],
                    "category": categories[w["cat"]],
                    "difficulty": "easy"
                }
            )
            if created:
                total_created += 1
            else:
                # Update if already exists (optional)
                word_obj.transliteration = w["trans"]
                word_obj.translation_uz = w["uz"]
                word_obj.category = categories[w["cat"]]
                word_obj.save()

        self.stdout.write(self.style.SUCCESS(f"Successfully seeded {total_created} new words. Total processed: {len(words_data)}"))
