from django.core.management.base import BaseCommand
from arab.models import PlacementQuestion, PlacementOption

class Command(BaseCommand):
    help = 'Seed placement test questions'

    def handle(self, *args, **options):
        # Clear existing to avoid duplicates or confusion
        questions_count = PlacementQuestion.objects.count()
        if questions_count > 0:
            self.stdout.write(self.style.WARNING(f"Found {questions_count} existing questions. Skipping delete to be safe, use update_or_create logic or manual clear."))
            # For simplicity in this build, we skip if already has data to avoid re-seeding on every deploy
            return

        questions = [
            {
                "text": "Arab tilida nechta harf bor?",
                "options": [
                    ("28 ta", True),
                    ("29 ta", False),
                    ("26 ta", False),
                    ("32 ta", False)
                ]
            },
            {
                "text": "Qaysi so'z 'Salom' degan ma'noni bildiradi?",
                "options": [
                    ("Assalomu alaykum", True),
                    ("Marhaban", False),
                    ("Shukran", False),
                    ("Kayfa haluk", False)
                ]
            },
            {
                "text": "Qaysi harf 'B' (Ba) harfi?",
                "options": [
                    ("ب", True),
                    ("ت", False),
                    ("ث", False),
                    ("ن", False)
                ]
            },
            {
                "text": "'Kitob' so'zining arabcha tarjimasi nima?",
                "options": [
                    ("Kitabun (كِتَابٌ)", True),
                    ("Qalamun (قَلَمٌ)", False),
                    ("Maktabun (مَمَكْتَبٌ)", False),
                    ("Babun (بَابٌ)", False)
                ]
            },
            {
                "text": "Arab yozuvi qaysi tomondan yoziladi?",
                "options": [
                    ("O'ngdan chapga", True),
                    ("Chapdan o'ngga", False),
                    ("Tepadan pastga", False),
                    ("Farqi yo'q", False)
                ]
            },
            {
                "text": "Qaysi so'z muzakkar (erkak) jinsida?",
                "options": [
                    ("Qalamun (قَلَمٌ)", True),
                    ("Sayyaratun (سَيَّارَةٌ)", False),
                    ("Madrasatun (مَدْرَسَةٌ)", False),
                    ("Bintun (بِنْتٌ)", False)
                ]
            },
            {
                "text": "'Ana' (أَنَا) olmoshi nimani bildiradi?",
                "options": [
                    ("Men", True),
                    ("Sen", False),
                    ("U", False),
                    ("Biz", False)
                ]
            },
            {
                "text": "'Haza' (هَذَا) so'zining ma'nosi?",
                "options": [
                    ("Bu (muzakkar)", True),
                    ("Bu (muannas)", False),
                    ("Ular", False),
                    ("Ana u", False)
                ]
            },
            {
                "text": "Qaysi jumla to'g'ri (Ismiy jumla)?",
                "options": [
                    ("Al-qalamu jadidun (Qalam yangidir)", True),
                    ("Jadidun al-qalamu", False),
                    ("Al-qalamu jadidan", False),
                    ("Qalamun al-jadidu", False)
                ]
            },
            {
                "text": "Fe'lning o'tgan zamon shaklini toping (U yozdi):",
                "options": [
                    ("Kataba (كَتَبَ)", True),
                    ("Yaktubu (يَكْتُبُ)", False),
                    ("Uktub (اُكْتُبْ)", False),
                    ("Katibun (كَاتِبٌ)", False)
                ]
            },
            {
                "text": "'Man' (مَنْ) so'roq yuklamasi nima uchun ishlatiladi?",
                "options": [
                    ("Odamlar (kim?) uchun", True),
                    ("Narsalar (nima?) uchun", False),
                    ("Vaqt (qachon?) uchun", False),
                    ("Joy (qayer?) uchun", False)
                ]
            },
            {
                "text": "Izofa (qaratqich kelishigi) qaysi misolda to'g'ri berilgan?",
                "options": [
                    ("Kitabu Zaydin (Zaydning kitobi)", True),
                    ("Kitabun Zaydun", False),
                    ("Al-kitabu Zaydin", False),
                    ("Kitabu Zaydan", False)
                ]
            }
        ]

        count = 0
        for q_data in questions:
            q = PlacementQuestion.objects.create(text=q_data["text"])
            for opt_text, is_correct in q_data["options"]:
                PlacementOption.objects.create(question=q, text=opt_text, is_correct=is_correct)
            count += 1
            self.stdout.write(f"Added question: {q.text}")

        self.stdout.write(self.style.SUCCESS(f"Successfully seeded {count} placement questions."))
