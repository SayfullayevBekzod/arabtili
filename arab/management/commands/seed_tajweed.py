from django.core.management.base import BaseCommand
from arab.models import TajweedRule, TajweedExample, TajweedMark, Word, TajweedTag
from django.utils.text import slugify

class Command(BaseCommand):
    help = "Seed Tajweed rules and examples"

    def handle(self, *args, **kwargs):
        self.stdout.write("Seeding Tajweed data...")
        
        # 1. Noon Saakin based rules
        rules_data = [
            {
                "title": "Idgham (Birlashuv)",
                "level": "A1",
                "short_desc": "Noon sakin yoki tanvin kelganda harfning qo'shilib o'qilishi.",
                "explanation": """Idgham – 'kirgizmoq' degan ma'noni bildiradi. 
                Agar Nun sakin (n) yoki Tanvin dan keyin (y, r, m, l, w, n) harflaridan biri kelsa, 
                Nun tovushi keyingi harfga kirishib ketadi.""",
                "examples": [
                    {"arabic": "مَن يَقُولُ", "translit": "May-yaqulu", "desc": "Nun harfi Y harfiga kirishib, g'unna bilan o'qiladi."},
                    {"arabic": "مِن رَّبِّهِم", "translit": "Mir-rabbihim", "desc": "Nun harfi R harfiga to'liq kirishib ketadi (g'unnasiz)."}
                ]
            },
            {
                "title": "Iqlab (Almashish)",
                "level": "A1",
                "short_desc": "Noon sakin yoki tanvin B harfiga yo'liqsa M ga aylanadi.",
                "explanation": """Iqlab – 'o'zgartirish'. Agar Nun sakin yoki Tanvin dan keyin Ba (ب) harfi kelsa,
                Nun tovushi Mim (م) tovushiga aylanadi va g'unna bilan o'qiladi.""",
                "examples": [
                    {"arabic": "مِن بَعْدِ", "translit": "Mim-ba'di", "desc": "Min ba'di emas, Mim ba'di deb o'qiladi."}
                ]
            },
            {
                "title": "Izhar (Aniq o'qish)",
                "level": "A1",
                "short_desc": "Noon sakindan keyin halqum harflari kelsa aniq o'qiladi.",
                "explanation": """Izhar – 'bildirish, aniq qilish'. Agar Nun sakin yoki Tanvin dan keyin
                Halqum harflari (Hamza, Ha, Ayn, Ha, Ghayn, Kha) kelsa, g'unna qilinmaydi, aniq o'qiladi.""",
                "examples": [
                    {"arabic": "مَنْ آمَنَ", "translit": "Man amana", "desc": "N aniq o'qiladi."}
                ]
            },
            {
                "title": "Ikhfa (Yashirish)",
                "level": "A2",
                "short_desc": "Noon sakin o'zidan keyingi harfga yashirinadi (g'unna bilan).",
                "explanation": """Ikhfa – 'yashirish'. Nun sakin yoki Tanvin dan keyin 15 ta harfdan biri kelsa 
                (t, th, j, d, dh, z, s, sh, s, d, t, z, f, q, k), 
                N tovushi to'liq aytilmaydi, balki burun orqali g'unna qilib yashiriladi.""",
                "examples": [
                    {"arabic": "أَنفُسَهُمْ", "translit": "An-fusahum", "desc": "N to'liq aytilmaydi, F ga yaqinlashadi."}
                ]
            },
            {
                "title": "Qalqalah (Tebratish)",
                "level": "A1",
                "short_desc": "5 ta harf (q, t, b, j, d) sukunli kelganda tebratib o'qiladi.",
                "explanation": """Qalqalah harflari: Qof, To, Ba, Jim, Dal (kutbu jad).
                Agar bu harflar sukunli kelsa, ularni tebratib, aks sado bilan o'qish kerak.""",
                "examples": [
                    {"arabic": "قُلْ هُوَ اللَّهُ أَحَدٌ", "translit": "Ahad", "desc": "Dal harfi to'xtaganda tebratiladi."}
                ]
            }
        ]

        for r_data in rules_data:
            rule, created = TajweedRule.objects.update_or_create(
                title=r_data["title"],
                defaults={
                    "short_desc": r_data["short_desc"],
                    "explanation": r_data["explanation"],
                    "slug": slugify(r_data["title"]),
                    "level": r_data["level"],
                    "is_published": True
                }
            )
            
            for ex_data in r_data["examples"]:
                TajweedExample.objects.get_or_create(
                    rule=rule,
                    arabic_text=ex_data["arabic"],
                    defaults={
                        "transliteration": ex_data["translit"],
                        "description": ex_data["desc"]
                    }
                )

        self.stdout.write(self.style.SUCCESS("Tajweed data seeded successfully!"))
