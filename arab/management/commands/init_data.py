from django.core.management.base import BaseCommand
from arab.models import (
    Word, VocabularyCategory, PlacementQuestion, PlacementOption, Course, Unit, Lesson,
    ScenarioCategory, Scenario, DialogLine, PhrasebookEntry, DailyQuest
)
import json
import os
from django.conf import settings

class Command(BaseCommand):
    help = 'Initialize all project data (Words, Placement, Courses, Tajweed, Scenarios)'

    def handle(self, *args, **options):
        self.stdout.write("Starting data initialization...")
        
        # 1. Load Words
        self.seed_dictionary()

        # 2. Seed Placement Test
        self.seed_placement()

        # 3. Ensure Basic Courses exist
        self.seed_courses()
        self.seed_tajweed()
        self.seed_quests()
        self.seed_scenarios()
        self.seed_extra_words()

        self.stdout.write(self.style.SUCCESS("Data initialization complete!"))

    def seed_dictionary(self):
        """Seed 100+ Arabic-Uzbek words"""
        categories_data = {
            "Salomlashish": [
                ("السَّلَامُ عَلَيْكُم", "Assalomu alaykum", "Salom (rasmiy)"),
                ("مَرْحَبًا", "Marhaban", "Salom"),
                ("صَبَاحُ الْخَيْر", "Sobahul-xayr", "Xayrli tong"),
                ("مَسَاءُ الْخَيْر", "Masaul-xayr", "Xayrli oqshom"),
                ("كَيْفَ حَالُكَ", "Kayfa holuk", "Qanday hollar?"),
                ("شُكْرًا", "Shukran", "Rahmat"),
                ("عَفْوًا", "Afwan", "Arzimaydi"),
                ("مَعَ السَّلَامَة", "Maas-salama", "Xayr"),
            ],
            "Oila": [
                ("أَب", "Ab", "Ota"),
                ("أُم", "Umm", "Ona"),
                ("اِبْن", "Ibn", "O'g'il"),
                ("بِنْت", "Bint", "Qiz"),
                ("أَخ", "Ax", "Aka/Uka"),
                ("أُخْت", "Uxt", "Opa/Singil"),
                ("جَدّ", "Jadd", "Buva"),
                ("جَدَّة", "Jadda", "Buvi"),
                ("زَوْج", "Zawj", "Er"),
                ("زَوْجَة", "Zawja", "Xotin"),
            ],
            "Raqamlar": [
                ("وَاحِد", "Wahid", "Bir"),
                ("اِثْنَان", "Isnon", "Ikki"),
                ("ثَلَاثَة", "Salasa", "Uch"),
                ("أَرْبَعَة", "Arba'a", "To'rt"),
                ("خَمْسَة", "Xamsa", "Besh"),
                ("سِتَّة", "Sitta", "Olti"),
                ("سَبْعَة", "Sab'a", "Yetti"),
                ("ثَمَانِيَة", "Samaniya", "Sakkiz"),
                ("تِسْعَة", "Tis'a", "To'qqiz"),
                ("عَشَرَة", "Ashara", "O'n"),
            ],
            "Ranglar": [
                ("أَحْمَر", "Ahmar", "Qizil"),
                ("أَزْرَق", "Azraq", "Ko'k"),
                ("أَخْضَر", "Axdar", "Yashil"),
                ("أَصْفَر", "Asfar", "Sariq"),
                ("أَبْيَض", "Abyad", "Oq"),
                ("أَسْوَد", "Aswad", "Qora"),
            ],
            "Maktab": [
                ("كِتَاب", "Kitab", "Kitob"),
                ("قَلَم", "Qalam", "Qalam"),
                ("دَفْتَر", "Daftar", "Daftar"),
                ("مَدْرَسَة", "Madrasa", "Maktab"),
                ("مُعَلِّم", "Muallim", "O'qituvchi"),
                ("طَالِب", "Tolib", "O'quvchi"),
                ("صَفّ", "Saff", "Sinf"),
                ("سَبُّورَة", "Sabbura", "Doska"),
            ],
            "Uy": [
                ("بَيْت", "Bayt", "Uy"),
                ("غُرْفَة", "Gurfa", "Xona"),
                ("بَاب", "Bab", "Eshik"),
                ("نَافِذَة", "Nafiza", "Deraza"),
                ("مِطْبَخ", "Mitbax", "Oshxona"),
                ("حَمَّام", "Hammam", "Hammom"),
                ("سَرِير", "Sarir", "Karavot"),
                ("كُرْسِي", "Kursi", "Stul"),
                ("طَاوِلَة", "Tovila", "Stol"),
            ],
            "Ovqatlar": [
                ("خُبْز", "Xubz", "Non"),
                ("مَاء", "Ma'", "Suv"),
                ("حَلِيب", "Halib", "Sut"),
                ("لَحْم", "Lahm", "Go'sht"),
                ("دَجَاج", "Dajaj", "Tovuq"),
                ("سَمَك", "Samak", "Baliq"),
                ("أَرُز", "Aruz", "Guruch"),
                ("فَاكِهَة", "Fokiha", "Meva"),
                ("خُضَار", "Xudar", "Sabzavot"),
                ("شَاي", "Shay", "Choy"),
                ("قَهْوَة", "Qahwa", "Qahva"),
            ],
            "Tabiat": [
                ("شَمْس", "Shams", "Quyosh"),
                ("قَمَر", "Qamar", "Oy"),
                ("سَمَاء", "Sama'", "Osmon"),
                ("أَرْض", "Ard", "Yer"),
                ("مَاء", "Ma'", "Suv"),
                ("نَار", "Nar", "Olov"),
                ("شَجَرَة", "Shajara", "Daraxt"),
                ("وَرْد", "Ward", "Gul"),
                ("بَحْر", "Bahr", "Dengiz"),
                ("جَبَل", "Jabal", "Tog'"),
            ],
            "Vaqt": [
                ("يَوْم", "Yawm", "Kun"),
                ("لَيْل", "Layl", "Tun"),
                ("صَبَاح", "Sabah", "Ertalab"),
                ("مَسَاء", "Masa'", "Kechqurun"),
                ("أُسْبُوع", "Usbu'", "Hafta"),
                ("شَهْر", "Shahr", "Oy"),
                ("سَنَة", "Sana", "Yil"),
                ("سَاعَة", "Sa'a", "Soat"),
                ("دَقِيقَة", "Daqiqa", "Daqiqa"),
            ],
            "Fe'llar": [
                ("كَتَبَ", "Kataba", "Yozdi"),
                ("قَرَأَ", "Qara'a", "O'qidi"),
                ("ذَهَبَ", "Zahaba", "Ketdi"),
                ("جَاءَ", "Ja'a", "Keldi"),
                ("أَكَلَ", "Akala", "Yedi"),
                ("شَرِبَ", "Shariba", "Ichdi"),
                ("نَامَ", "Nama", "Uxladi"),
                ("سَمِعَ", "Sami'a", "Eshitdi"),
                ("رَأَى", "Ra'a", "Ko'rdi"),
                ("قَالَ", "Qola", "Dedi"),
                ("فَعَلَ", "Fa'ala", "Qildi"),
                ("عَرَفَ", "Arafa", "Bildi"),
            ],
            "Tana a'zolari": [
                ("رَأْس", "Ra's", "Bosh"),
                ("عَيْن", "Ayn", "Ko'z"),
                ("أُذُن", "Uzun", "Quloq"),
                ("أَنْف", "Anf", "Burun"),
                ("فَم", "Fam", "Og'iz"),
                ("يَد", "Yad", "Qo'l"),
                ("رِجْل", "Rijl", "Oyoq"),
                ("قَلْب", "Qalb", "Yurak"),
                ("بَطْن", "Batn", "Qorin"),
                ("ظَهْر", "Zahr", "Orqa"),
            ],
            "Hayvonlar": [
                ("قِطّ", "Qitt", "Mushuk"),
                ("كَلْب", "Kalb", "It"),
                ("حِصَان", "Hison", "Ot"),
                ("بَقَرَة", "Baqara", "Sigir"),
                ("خَرُوف", "Xaruf", "Qo'y"),
                ("دَجَاجَة", "Dajaja", "Tovuq"),
                ("أَسَد", "Asad", "Arslon"),
                ("فِيل", "Fil", "Fil"),
                ("طَيْر", "Tayr", "Qush"),
                ("سَمَكَة", "Samaka", "Baliq"),
            ],
            "Kasblar": [
                ("طَبِيب", "Tabib", "Shifokor"),
                ("مُهَنْدِس", "Muhandis", "Muhandis"),
                ("مُدَرِّس", "Mudarris", "O'qituvchi"),
                ("شُرْطِي", "Shurti", "Politsiyachi"),
                ("طَيَّار", "Tayyar", "Uchuvchi"),
                ("مُحَامِي", "Muhami", "Advokat"),
                ("تَاجِر", "Tajir", "Savdogar"),
                ("فَلَّاح", "Fallah", "Dehqon"),
                ("صَحَفِي", "Sahafi", "Jurnalist"),
                ("سَائِق", "Sa'iq", "Haydovchi"),
            ],
            "So'roq so'zlari": [
                ("مَنْ", "Man", "Kim?"),
                ("مَا", "Ma", "Nima?"),
                ("أَيْنَ", "Ayna", "Qayerda?"),
                ("مَتَى", "Mata", "Qachon?"),
                ("كَيْفَ", "Kayfa", "Qanday?"),
                ("لِمَاذَا", "Limaza", "Nima uchun?"),
                ("كَمْ", "Kam", "Qancha?"),
                ("أَيّ", "Ayy", "Qaysi?"),
                ("هَلْ", "Hal", "...mi? (so'roq)"),
            ],
            "Kunlar": [
                ("الْأَحَد", "Al-ahad", "Yakshanba"),
                ("الْاِثْنَيْن", "Al-isnayn", "Dushanba"),
                ("الثُّلَاثَاء", "As-sulasa'", "Seshanba"),
                ("الْأَرْبِعَاء", "Al-arbi'a'", "Chorshanba"),
                ("الْخَمِيس", "Al-xamis", "Payshanba"),
                ("الْجُمْعَة", "Al-jum'a", "Juma"),
                ("السَّبْت", "As-sabt", "Shanba"),
            ],
        }
        
        total = 0
        for cat_name, words in categories_data.items():
            category, _ = VocabularyCategory.objects.get_or_create(name=cat_name)
            for arabic, translit, uzbek in words:
                _, created = Word.objects.get_or_create(
                    arabic=arabic,
                    defaults={
                        'transliteration': translit,
                        'translation_uz': uzbek,
                        'category': category
                    }
                )
                if created: total += 1
        self.stdout.write(f"Seeded {total} dictionary words.")

    def seed_placement(self):
        if PlacementQuestion.objects.exists():
            self.stdout.write("Placement questions already exist. Skipping.")
            return

        questions = [
            {"text": "Arab tilida nechta harf bor?", "options": [("28 ta", True), ("29 ta", False), ("26 ta", False), ("32 ta", False)]},
            {"text": "Qaysi so'z 'Salom' degan ma'noni bildiradi?", "options": [("Assalomu alaykum", True), ("Marhaban", False), ("Shukran", False), ("Kayfa haluk", False)]},
            {"text": "Qaysi harf 'B' (Ba) harfi?", "options": [("ب", True), ("ت", False), ("ث", False), ("ن", False)]},
            {"text": "'Kitob' so'zining arabcha tarjimasi nima?", "options": [("Kitabun (كِتَابٌ)", True), ("Qalamun (قَلَمٌ)", False), ("Maktabun (مَكْتَبٌ)", False), ("Babun (بَابٌ)", False)]},
            {"text": "Arab yozuvi qaysi tomondan yoziladi?", "options": [("O'ngdan chapga", True), ("Chapdan o'ngga", False), ("Tepadan pastga", False), ("Farqi yo'q", False)]},
            {"text": "Qaysi so'z muzakkar (erkak) jinsida?", "options": [("Qalamun (قَلَمٌ)", True), ("Sayyaratun (سَيَّارَةٌ)", False), ("Madrasatun (مَدْرَسَةٌ)", False), ("Bintun (بِنْتٌ)", False)]},
            {"text": "'Ana' (أَنَا) olmoshi nimani bildiradi?", "options": [("Men", True), ("Sen", False), ("U", False), ("Biz", False)]},
            {"text": "'Haza' (هَذَا) so'zining ma'nosi?", "options": [("Bu (muzakkar)", True), ("Bu (muannas)", False), ("Ular", False), ("Ana u", False)]},
            {"text": "Qaysi jumla to'g'ri (Ismiy jumla)?", "options": [("Al-qalamu jadidun (Qalam yangidir)", True), ("Jadidun al-qalamu", False), ("Al-qalamu jadidan", False), ("Qalamun al-jadidu", False)]},
            {"text": "Fe'lning o'tgan zamon shaklini toping (U yozdi):", "options": [("Kataba (كَتَبَ)", True), ("Yaktubu (يَكْتُبُ)", False), ("Uktub (اُكْتُبْ)", False), ("Katibun (كَاتِبٌ)", False)]},
            {"text": "'Man' (مَنْ) so'roq yuklamasi nima uchun ishlatiladi?", "options": [("Odamlar (kim?) uchun", True), ("Narsalar (nima?) uchun", False), ("Vaqt (qachon?) uchun", False), ("Joy (qayer?) uchun", False)]},
            {"text": "Izofa (qaratqich kelishigi) qaysi misolda to'g'ri berilgan?", "options": [("Kitabu Zaydin (Zaydning kitobi)", True), ("Kitabun Zaydun", False), ("Al-kitabu Zaydin", False), ("Kitabu Zaydan", False)]},
        ]

        for q_data in questions:
            q, _ = PlacementQuestion.objects.get_or_create(text=q_data["text"])
            if not q.options.exists():
                for opt_text, is_correct in q_data["options"]:
                    PlacementOption.objects.create(question=q, text=opt_text, is_correct=is_correct)
        
        self.stdout.write(f"Seeded {len(questions)} placement questions.")

    def seed_courses(self):
        courses_data = [
            ("Arab tili asoslari", "A0", "Ushbu kurs arab tilini mutlaqo noldan boshlayotganlar uchun. Alifbo, asosiy so'zlar va oddiy iboralarni o'rganasiz."),
            ("Arab tili: Boshlang'ich A1", "A1", "Arab tilini noldan o'rganuvchilar uchun mukammal kurs. Grammatika va kundalik suhbatlarni o'z ichiga oladi."),
            ("O'rta Daraja (A2)", "A2", "Qur'on o'qishni interaktiv usulda o'rganing. Tajvid qoidalari va amaliy mashqlar."),
            ("Mukammal Arab Tili (B1)", "B1", "Ilg'or grammatika, adabiyot va murakkab matnlarni tushunish."),
        ]
        for title, level, desc in courses_data:
            course, created = Course.objects.update_or_create(
                level=level, 
                defaults={"title": title, "description": desc, "is_published": True}
            )
            # Add sample units/lessons if new
            if created:
                unit, _ = Unit.objects.get_or_create(course=course, order=1, defaults={"title": f"{level} - 1-modul"})
                Lesson.objects.get_or_create(unit=unit, order=1, defaults={"title": "Kirish darsi", "theory": "Bu darsda asosiy tushunchalar bilan tanishasiz."})
        self.stdout.write("Courses seeded with units/lessons.")

    def seed_quests(self):
        defaults = [
            {"title": "O'quvchi", "description": "10 XP yig'ing", "type": "XP", "target": 10, "reward": 5},
            {"title": "Bilimdon", "description": "50 XP yig'ing", "type": "XP", "target": 50, "reward": 20},
            {"title": "Mutaxassis", "description": "100 XP yig'ing", "type": "XP", "target": 100, "reward": 50},
            {"title": "Yangi qadam", "description": "1 ta darsni tugating", "type": "LESSON", "target": 1, "reward": 15},
            {"title": "Takrorlash", "description": "10 ta so'zni takrorlang", "type": "REVIEW", "target": 10, "reward": 10},
        ]
        
        created_count = 0
        for data in defaults:
            obj, created = DailyQuest.objects.get_or_create(
                title=data["title"],
                defaults={
                    "description": data["description"],
                    "quest_type": data["type"],
                    "target_amount": data["target"],
                    "reward_xp": data["reward"]
                }
            )
            if created: created_count += 1
        self.stdout.write(f"Seeded {created_count} daily quests.")

    def seed_scenarios(self):
        """Seed conversation scenarios and dialogs"""
        scenarios_data = [
            {
                "category": "Do'konda",
                "icon": "fas fa-shopping-cart",
                "scenarios": [
                    {
                        "title": "Meva do'konida",
                        "difficulty": "beginner",
                        "dialogs": [
                            ("Sotuvchi", "مَرْحَبًا، كَيْفَ أُسَاعِدُكَ؟", "Salom, sizga qanday yordam bera olaman?", False),
                            ("Xaridor", "أُرِيدُ تُفَّاحًا", "Men olma xohlayman", True),
                            ("Sotuvchi", "كَمْ كِيلُو؟", "Necha kilo?", False),
                            ("Xaridor", "كِيلُو وَاحِد، مِنْ فَضْلِكَ", "Bir kilo, iltimos", True),
                            ("Sotuvchi", "تَفَضَّلْ، هَذَا خَمْسَة رِيَال", "Marhamat, bu besh riyal", False),
                            ("Xaridor", "شُكْرًا", "Rahmat", True),
                        ],
                        "phrases": [
                            ("كَمْ هَذَا؟", "Bu qancha?"),
                            ("أُرِيدُ...", "Men ... xohlayman"),
                            ("هَلْ عِنْدَكَ...؟", "Sizda ... bormi?"),
                        ]
                    }
                ]
            },
            {
                "category": "Restoranda",
                "icon": "fas fa-utensils",
                "scenarios": [
                    {
                        "title": "Buyurtma berish",
                        "difficulty": "beginner",
                        "dialogs": [
                            ("Ofitsiant", "أَهْلًا وَسَهْلًا، مَاذَا تُرِيدُ؟", "Xush kelibsiz, nima xohlaysiz?", False),
                            ("Xaridor", "أُرِيدُ قَائِمَةَ الطَّعَام", "Menyu ko'rsam bo'ladimi", True),
                            ("Ofitsiant", "تَفَضَّلْ", "Marhamat", False),
                            ("Xaridor", "أُرِيدُ دَجَاجًا مَعَ أَرُز", "Tovuq va guruch xohlayman", True),
                            ("Ofitsiant", "وَمَاذَا تَشْرَبُ؟", "Nima ichmoqchisiz?", False),
                            ("Xaridor", "عَصِير بُرْتُقَال", "Apelsin sharbati", True),
                        ],
                        "phrases": [
                            ("الْحِسَاب، مِنْ فَضْلِكَ", "Hisob, iltimos"),
                            ("لَذِيذ جِدًّا", "Juda mazali"),
                        ]
                    }
                ]
            },
            {
                "category": "Sayohatda",
                "icon": "fas fa-plane",
                "scenarios": [
                    {
                        "title": "Aeroportda",
                        "difficulty": "intermediate",
                        "dialogs": [
                            ("Xodim", "جَوَازُ السَّفَر، مِنْ فَضْلِكَ", "Pasportingizni bering, iltimos", False),
                            ("Sayohatchi", "تَفَضَّلْ", "Marhamat", True),
                            ("Xodim", "مَا هِيَ وِجْهَتُكَ؟", "Qayerga borasiz?", False),
                            ("Sayohatchi", "أَنَا ذَاهِبٌ إِلَى دُبَيّ", "Men Dubayga ketyapman", True),
                        ],
                        "phrases": [
                            ("أَيْنَ بَوَّابَة...؟", "...darvoza qayerda?"),
                            ("الطَّائِرَة", "Samolyot"),
                        ]
                    }
                ]
            },
        ]
        
        total_dialogs = 0
        for cat_data in scenarios_data:
            category, _ = ScenarioCategory.objects.get_or_create(
                name=cat_data["category"],
                defaults={"icon": cat_data["icon"]}
            )
            for scen in cat_data["scenarios"]:
                scenario, _ = Scenario.objects.get_or_create(
                    category=category,
                    title=scen["title"],
                    defaults={"difficulty": scen["difficulty"]}
                )
                for i, (char, arabic, uzbek, is_user) in enumerate(scen["dialogs"]):
                    DialogLine.objects.get_or_create(
                        scenario=scenario,
                        order=i+1,
                        defaults={
                            "character_name": char,
                            "text_arabic": arabic,
                            "text_uz": uzbek,
                            "is_user_line": is_user
                        }
                    )
                    total_dialogs += 1
                for arabic, uzbek in scen.get("phrases", []):
                    PhrasebookEntry.objects.get_or_create(
                        category=category,
                        scenario=scenario,
                        text_arabic=arabic,
                        defaults={"text_uz": uzbek}
                    )
        self.stdout.write(f"Seeded {total_dialogs} dialog lines.")

    def seed_tajweed(self):
        from arab.models import TajweedRule, TajweedExample, TajweedQuiz, TajweedQuizOption
        rules = [
            {
                "slug": "nuun-sakinah",
                "title": "Nuun Sakinah va Tanween",
                "category": "noon_sakinah",
                "short_desc": "Sukunli Nun va Tanvin qoidalari",
                "explanation": "Sukunli nun (نْ) yoki tanvindan so'ng keladigan harfga qarab 4 xil qoida bor: Izhor, Idg'om, Iqlob, Ixfo.",
                "examples": [
                    ("مِنْ خَوْفٍ", "Min xovfin", "Izhor: Nun dan keyin xoi harfi keldi"),
                    ("مَنْ يَعْمَلْ", "Man ya'mal", "Idg'om: Nun dan keyin yo harfi keldi"),
                ]
            },
            {
                "slug": "qolqola",
                "title": "Qolqola",
                "category": "alphabet",
                "short_desc": "Tebranib chiqadigan harflar",
                "explanation": "Qolqola harflari beshta: ق ط ب ج د. Bular sukunli bo'lib kelsa tebratib o'qiladi.",
                "examples": [
                    ("قُلْ أَعُوذُ بِرَبِّ الْفَلَقِ", "Al-falaq", "Oxirgi Qof harfida qolqola qilinadi"),
                    ("أَمْ لَمْ يُولَدْ", "Yulad", "Dal harfida qolqola"),
                ]
            },
            {
                "slug": "meem-sakinah",
                "title": "Meem Sakinah",
                "category": "meem_sakinah",
                "short_desc": "Sukunli Mim qoidalari",
                "explanation": "Sukunli mimdan so'ng boshqa bir mim kelsa Idg'om, bo harfi kelsa Ixfo, qolganlarida Izhor bo'ladi.",
                "examples": [
                    ("أَمْ لَمْ تُنْذِرْهُمْ", "Am lam", "Mim dan so'ng Lom kelgani uchun Izhor"),
                    ("تَرْمِيهِمْ بِحِجَارَةٍ", "Tarmihim bi", "Mim dan so'ng Bo kelgani uchun Ixfo"),
                ]
            }
        ]
        for r_data in rules:
            rule, _ = TajweedRule.objects.update_or_create(
                slug=r_data["slug"],
                defaults={
                    "title": r_data["title"],
                    "category": r_data["category"],
                    "short_desc": r_data["short_desc"],
                    "explanation": r_data["explanation"]
                }
            )
            for arabic, translit, desc in r_data["examples"]:
                TajweedExample.objects.get_or_create(
                    rule=rule,
                    arabic_text=arabic,
                    defaults={"transliteration": translit, "description": desc}
                )
        self.stdout.write("Tajweed rules seeded.")

    def seed_extra_words(self):
        json_path = os.path.join(settings.BASE_DIR, 'words_new.json')
        if not os.path.exists(json_path):
            return
        
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            
        count = 0
        for item in data:
            cat_name = item.get('category', 'General')
            category, _ = VocabularyCategory.objects.get_or_create(name=cat_name)
            _, created = Word.objects.get_or_create(
                arabic=item['arabic'],
                defaults={
                    'transliteration': item.get('transliteration', ''),
                    'translation_uz': item.get('translation_uz', ''),
                    'category': category
                }
            )
            if created: count += 1
        self.stdout.write(f"Imported {count} extra words from JSON.")

