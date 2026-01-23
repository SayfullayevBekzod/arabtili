from django.core.management.base import BaseCommand
from arab.models import TajweedRule, TajweedExample
from django.utils.text import slugify

class Command(BaseCommand):
    help = "Seed comprehensive Tajweed content with categories and many examples"

    def handle(self, *args, **kwargs):
        self.stdout.write("Expanding Tajweed content...")

        tajweed_data = [
            # NOON SAKINAH & TANWEEN
            {
                "category": "noon_sakinah",
                "title": "Izhor (Aniq o'qish)",
                "slug": "izhor",
                "level": "A1",
                "short_desc": "Noon sakin yoki tanvindan keyin halqum harflari kelsa, Noon aniq o'qiladi.",
                "explanation": "Izhor 'aniq qilish' degani. Noon sokin (نْ) yoki tanwin (ً ٍ ٌ) dan keyin 6 ta halqum harfi (ء ه ع ح غ خ) kelsa, g'unnasiz, Noon harfi aniq talaffuz qilinadi.",
                "examples": [
                    {"arabic": "مَنْ آمَنَ", "trans": "Kim iymon keltirsa", "desc": "Noon dan keyin Hamza kelgan."},
                    {"arabic": "أَنْعَمْتَ", "trans": "Sen ne'mat berding", "desc": "Noon dan keyin Ayn kelgan."},
                    {"arabic": "مِنْ حَيْثُ", "trans": "Qayerdanki", "desc": "Noon dan keyin Ha kelgan."},
                    {"arabic": "فَصَلِّ لِرَبِّكَ وَانْحَرْ", "trans": "Rabbing uchun namoz o'qi va qurbonlik qil", "desc": "Noon dan keyin Ha kelgan."},
                    {"arabic": "مِنْ غَيْرِ", "trans": "G'ayridan", "desc": "Noon dan keyin G'oyn kelgan."},
                    {"arabic": "مِنْ خَوْفٍ", "trans": "Xavfdan", "desc": "Noon dan keyin Xo kelgan."},
                    {"arabic": "قُلْ يَا أَيُّهَا الْكَافِرُونَ", "trans": "Ayting: Ey kofirlar", "desc": "Tamin (un) dan keyin Alif - Izhor."},
                    {"arabic": "كُفُوًا أَحَدٌ", "trans": "Unga hech kim teng emas", "desc": "Tanwin (an) dan keyin Hamza - Izhor."},
                ]
            },
            {
                "category": "noon_sakinah",
                "title": "Idgham (Birlashuv)",
                "slug": "idgham",
                "level": "A1",
                "short_desc": "Noon sakin yoki tanvinni keyingi harfga qo'shib o'qish.",
                "explanation": "Idgham 'kirgizish' degani. Noon sokin yoki tanwindan keyin 6 ta (ي ر م ل و ن) harf kelsa, Noon tovushi keyingi harfga qo'shib yuboriladi. \n1. G'unnali (ي ن م و) - Yarmaluna.\n2. G'unnasiz (ل ر).",
                "examples": [
                    {"arabic": "مَن يَقُولُ", "trans": "Kim aytadi", "desc": "G'unnali idgham (Y)."},
                    {"arabic": "مِن وَرَائِهِمْ", "trans": "Ularning ortidan", "desc": "G'unnali idgham (W)."},
                    {"arabic": "مِّن مَّاءٍ", "trans": "Suvdan", "desc": "G'unnali idgham (M)."},
                    {"arabic": "مِن نُّطْفَةٍ", "trans": "Nutfadan", "desc": "G'unnali idgham (N)."},
                    {"arabic": "مِن رَبِّهِمْ", "trans": "Rabbilaridan", "desc": "G'unnasiz idgham (R)."},
                    {"arabic": "مِن لَّدُنْهُ", "trans": "Uning huzuridan", "desc": "G'unnasiz idgham (L)."},
                    {"arabic": "خَيْرٌ لَّكُمْ", "trans": "Siz uchun yaxshidir", "desc": "Tanwin + L - G'unnasiz idgham."},
                ]
            },
            {
                "category": "noon_sakinah",
                "title": "Iqlab (Almashtirish)",
                "slug": "iqlab",
                "level": "A1",
                "short_desc": "Noon sakin yoki tanvin B harfiga yo'liqsa M ga aylanadi.",
                "explanation": "Iqlab 'o'zgartirish'. Noon sokin yoki tanwindan keyin faqat bitta 'Ba' (ب) harfi kelsa, Noon tovushi 'Meem'ga (م) aylanadi va g'unna qilinadi.",
                "examples": [
                    {"arabic": "مِن بَعْدِ", "trans": "Keyinchalik", "desc": "Mim-ba'di bo'lib o'qiladi."},
                    {"arabic": "أَنبِئْهُم", "trans": "Ularga xabar ber", "desc": "Ambi'hum bo'lib o'qiladi."},
                    {"arabic": "سَمِيعٌ بَصِيرٌ", "trans": "Eshituvchi va ko'ruvchi", "desc": "Samiy'um-basiyr bo'lib o'qiladi."},
                ]
            },
            {
                "category": "noon_sakinah",
                "title": "Ikhfa (Yashirish)",
                "slug": "ikhfa",
                "level": "A2",
                "short_desc": "Noon sakinni keyingi harf oldida yashirib o'qish.",
                "explanation": "Ikhfa 'yashirish'. Noon sokin yoki tanwindan keyin 15 ta harf kelsa, Noon tovushi to'liq aytilmaydi, balki burunda yashirib, g'unna bilan talaffuz qilinadi.",
                "examples": [
                    {"arabic": "أَنفُسَكُمْ", "trans": "O'zingizni", "desc": "Noon F harfida yashiriladi."},
                    {"arabic": "مِن دُونِ", "trans": "Dan boshqa", "desc": "Noon D harfida yashiriladi."},
                    {"arabic": "كُنتُمْ", "trans": "Sizlar edingiz", "desc": "Noon T harfida yashiriladi."},
                    {"arabic": "مِن سِجِّيلٍ", "trans": "Sijjiildan", "desc": "Noon S harfida yashiriladi."},
                    {"arabic": "عَدَابٌ شَدِيدٌ", "trans": "Qattiq azob", "desc": "Tanwin + Shin - Ikhfa."},
                    {"arabic": "قَوْلاً سَدِيدًا", "trans": "To'g'ri so'zni", "desc": "Tanwin + Seen - Ikhfa."},
                ]
            },

            # MEEM SAKINAH
            {
                "category": "meem_sakinah",
                "title": "Izhor Shafawi",
                "slug": "izhor-shafawi",
                "level": "A2",
                "short_desc": "Meem sakindan keyin M va B dan boshqa harf kelsa aniq o'qiladi.",
                "explanation": "Meem sokin (مْ) dan keyin 'Meem' (م) va 'Ba' (ب) dan boshqa barcha 26 ta harf kelsa, Meem aniq talaffuz qilinadi.",
                "examples": [
                    {"arabic": "لَكُمْ دِينُكُمْ", "trans": "Sizga o'z diningiz", "desc": "Meem dan keyi D kelgan."},
                    {"arabic": "أَمْ لَمْ تُنذِرْهُمْ", "trans": "Yoki ularni ogohlantirmadingmi", "desc": "Meem dan keyin L kelgan."},
                ]
            },
            {
                "category": "meem_sakinah",
                "title": "Ikhfa Shafawi",
                "slug": "ikhfa-shafawi",
                "level": "A2",
                "short_desc": "Meem sakindan keyin B harfi kelsa yashirib o'qiladi.",
                "explanation": "Meem sokin (مْ) dan keyin 'Ba' (ب) harfi kelsa, Meem harfi lablar orasida yashirilib, g'unna bilan o'qiladi.",
                "examples": [
                    {"arabic": "تَرْمِيهِم بِحِجَارَةٍ", "trans": "Ularni toshlar bilan uradi", "desc": "Meem va Ba uchrashishi."},
                ]
            },
            {
                "category": "meem_sakinah",
                "title": "Idgham Mithlayn",
                "slug": "idgham-mithlayn",
                "level": "A2",
                "short_desc": "Ikki Meem'ni bir-biriga qo'shib o'qish.",
                "explanation": "Meem sokin (مْ) dan keyin harakatli 'Meem' (مَ مُ مِ) kelsa, ikkalasi bitta tashdidli Meem bo'lib, g'unna bilan o'qiladi.",
                "examples": [
                    {"arabic": "لَهُم مَّا يَشَاءُونَ", "trans": "Ularga xohlagan narsalari bor", "desc": "Ikki Meem birlashishi."},
                ]
            },

            # MUDOOD (CHO'ZIQLAR)
            {
                "category": "mudood",
                "title": "Madd Tabiiy",
                "slug": "madd-tabiiy",
                "level": "A1",
                "short_desc": "Asliy cho'ziq - 2 harakat miqdorida.",
                "explanation": "Madd harflari (ا و ي) dan keyin cho'zilishga sabab bo'luvchi Hamza yoki Sukun kelmasa, harf 2 harakat miqdorida (tabiiy) cho'ziladi.",
                "examples": [
                    {"arabic": "قَالَ", "trans": "Aytdi", "desc": "Alif bilan cho'zilish."},
                    {"arabic": "يَقُولُ", "trans": "Aytadi", "desc": "Wov bilan cho'zilish."},
                    {"arabic": "قِيلَ", "trans": "Aytildi", "desc": "Ya bilan cho'zilish."},
                ]
            },
            {
                "category": "mudood",
                "title": "Madd Muttasil",
                "slug": "madd-muttasil",
                "level": "A2",
                "short_desc": "Bitta so'z ichida cho'ziq harfidan keyin Hamza kelsa.",
                "explanation": "Madd harfidan keyin Hamza (ء) bitta so'zning o'zida kelsa, u 4 yoki 5 harakat miqdorida cho'ziladi. Bu lozim (shart) cho'ziqdir.",
                "examples": [
                    {"arabic": "جَاءَ", "trans": "Keldi", "desc": "Alif + Hamza bitta so'zda."},
                    {"arabic": "السَّمَاءُ", "trans": "Osmon", "desc": "Alif + Hamza bitta so'zda."},
                ]
            },
            {
                "category": "mudood",
                "title": "Madd Munfassil",
                "slug": "madd-munfassil",
                "level": "A2",
                "short_desc": "Ikki xil so'z orasida cho'ziq harfidan keyin Hamza kelsa.",
                "explanation": "Madd harfi bitta so'z oxirida, Hamza esa keyingi so'z boshida kelsa, bu Madd Munfassil bo'ladi. U 2, 4 yoki 5 harakat miqdorida cho'zilishi mumkin.",
                "examples": [
                    {"arabic": "يَا أَيُّهَا", "trans": "Ey ...", "desc": "Ya so'zida Alif, keyingi so'zda Hamza."},
                    {"arabic": "فِي أَيِّ", "trans": "Qaysi ... da", "desc": "Fi so'zida Ya, keyingi so'zda Hamza."},
                ]
            },
            {
                "category": "mudood",
                "title": "Madd Lozim",
                "slug": "madd-lozim",
                "level": "B1",
                "short_desc": "Madd harfidan keyin doimiy (asliy) sukun kelsa.",
                "explanation": "Madd harfidan keyin asliy sukun (yoki tashdid) kelsa, u doimiy ravishda 6 harakat miqdorida cho'zilishi shart. Bu eng kuchli cho'ziq hisoblanadi.",
                "examples": [
                    {"arabic": "الضَّالِّينَ", "trans": "Adashganlar", "desc": "Alifdan keyin tashdidli Lom (asliy sukun)."},
                    {"arabic": "الْحَاقَّةُ", "trans": "Haqqo (Qiyomat)", "desc": "Alifdan keyin tashdidli Qof."},
                ]
            },

            # OTHER / QALQALAH
            {
                "category": "other",
                "title": "Qalqalah (Tebratish)",
                "slug": "qalqalah",
                "level": "A1",
                "short_desc": "5 ta harf sukunli kelganda tebratib o'qiladi.",
                "explanation": "Qof (ق), To (ط), Ba (ب), Jim (ج), Dal (د) - (قُطْبُ جَدٍ) harflari sukunli kelsa yoki so'z oxirida to'xtalganda sukunli bo'lib qolsa, ular tebratib, aks-sado berib o'qiladi.\n1. Kubro (Katta) - so'z oxirida to'xtalganda.\n2. Sug'ro (Kichik) - so'z o'rtasida.",
                "examples": [
                    {"arabic": "الْفَلَقِ", "trans": "Tong (Falaq)", "desc": "Katta qalqalah (so'z oxiri)."},
                    {"arabic": "لَمْ يَلِدْ", "trans": "Tug'madi", "desc": "Katta qalqalah (Dal)."},
                    {"arabic": "يَدْخُلُونَ", "trans": "Kiradilar", "desc": "Kichik qalqalah (Dal - so'z o'rtasi)."},
                    {"arabic": "خَلَقْنَا", "trans": "Yaratdik", "desc": "Kichik qalqalah (Qof)."},
                ]
            },

            # SIFATLAR
            {
                "category": "sifat",
                "title": "Hams (Pichirlash)",
                "slug": "hams",
                "level": "B1",
                "short_desc": "Harfni aytganda nafas chiqishi.",
                "explanation": "Fahaththahu shaxsun sakat (ف ح ث هـ ش خ ص س ك ت) harflari sukunli kelsa, havo (nafas) chiqib, pichirlash simon ovoz bilan aytiladi.",
                "examples": [
                    {"arabic": "أَفْوَاجًا", "trans": "To'p-to'p bo'lib", "desc": "Fe harfida nafas chiqishi."},
                    {"arabic": "يُوَسْوِسُ", "trans": "Vasvasa qiladi", "desc": "Seen harfida nafas chiqishi."},
                ]
            }
        ]

        for r_data in tajweed_data:
            # Update or create rule
            rule, created = TajweedRule.objects.update_or_create(
                slug=r_data["slug"],
                defaults={
                    "title": r_data["title"],
                    "category": r_data["category"],
                    "level": r_data["level"],
                    "short_desc": r_data["short_desc"],
                    "explanation": r_data["explanation"],
                    "is_published": True,
                }
            )
            
            # Add examples
            for ex in r_data["examples"]:
                TajweedExample.objects.get_or_create(
                    rule=rule,
                    arabic_text=ex["arabic"],
                    defaults={
                        "translation_uz": ex["trans"],
                        "description": ex["desc"]
                    }
                )

        self.stdout.write(self.style.SUCCESS(f"Successfully expanded Tajweed content with {len(tajweed_data)} rules."))
