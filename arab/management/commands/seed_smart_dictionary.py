import os
import asyncio
import time
from django.core.management.base import BaseCommand
from django.conf import settings
from django.core.files.base import ContentFile
from arab.models import Word, VocabularyCategory

# Male Arabic Voice from Microsoft Edge TTS
ARABIC_MALE_VOICE = "ar-SA-HamedNeural"

class Command(BaseCommand):
    help = "Lug'atni avtomatik to'ldirish va ERKAK ovozida audio yaratish (edge-tts)"

    def handle(self, *args, **options):
        # 0. Check edge-tts
        try:
            import edge_tts
        except ImportError:
            self.stdout.write(self.style.ERROR("'edge-tts' kutubxonasi kerak."))
            self.stdout.write(self.style.WARNING("O'rnating: pip install edge-tts"))
            return

        self.stdout.write(self.style.SUCCESS("Boshlanmoqda... 🚀 (Erkak ovozi bilan)"))

        # DATASET: Categories and Words
        dataset = {
            "Salomlashish (Greetings)": [
                ("marhaban", "مَرحَبًا", "Salom"),
                ("assalamu alaykum", "السَّلَامُ عَلَيْكُم", "Assalomu alaykum"),
                ("wa alaykum assalam", "وَعَلَيْكُمُ السَّلَام", "Va alaykum assalom"),
                ("sabahul khayr", "صَبَاحُ الْخَيْر", "Xayrli tong"),
                ("masa'ul khayr", "مَسَاءُ الْخَيْر", "Xayrli kech"),
                ("kayfa haluk", "كَيْفَ حَالُكَ؟", "Ahvolingiz qanday?"),
                ("shukran", "شُكْرًا", "Rahmat"),
                ("afwan", "عَفْوًا", "Arzimaydi"),
                ("ila al-liqaa", "إِلَى اللِّقَاءِ", "Ko'rishguncha"),
                ("ma'a as-salama", "مَعَ السَّلَامَة", "Xayr (omonlik bilan)"),
            ],
            "Oila (Family)": [
                ("ab", "أَب", "Ota"),
                ("umm", "أُمّ", "Ona"),
                ("akh", "أَخ", "Aka/Uka"),
                ("ukht", "أُخْت", "Opa/Singil"),
                ("jadd", "جَدّ", "Bobo"),
                ("jadda", "جَدَّة", "Buvi"),
                ("ibn", "اِبْن", "O'g'il"),
                ("ibna", "اِبْنَة", "Qiz"),
                ("rajul", "رَجُل", "Erkak"),
                ("imra'a", "اِمْرَأَة", "Ayol"),
            ],
            "Ranglar (Colors)": [
                ("abyad", "أَبْيَض", "Oq"),
                ("aswad", "أَسْوَد", "Qora"),
                ("ahmar", "أَحْمَر", "Qizil"),
                ("azraq", "أَزْرَق", "Ko'k"),
                ("akhdar", "أَخْضَر", "Yashil"),
                ("asfar", "أَصْفَر", "Sariq"),
                ("burtuqali", "بُرْتُقَالِيّ", "Apelsin rang"),
                ("banafsaji", "بَنَفْسَجِيّ", "Binafsha"),
            ],
            "Raqamlar (Numbers)": [
                ("wahid", "وَاحِد", "Bir"),
                ("ithnan", "اِثْنَان", "Ikki"),
                ("thalatha", "ثَلَاثَة", "Uch"),
                ("arba'a", "أَرْبَعَة", "To'rt"),
                ("khamsa", "خَمْسَة", "Besh"),
                ("sitta", "سِتَّة", "Olti"),
                ("sab'a", "سَبْعَة", "Yetti"),
                ("thamaniya", "ثَمَانِيَة", "Sakkiz"),
                ("tis'a", "تِسْعَة", "To'qqiz"),
                ("ashara", "عَشَرَة", "O'n"),
            ],
            "Maktab (School)": [
                ("kitab", "كِتَاب", "Kitob"),
                ("qalam", "قَلَم", "Qalam"),
                ("maktab", "مَكْتَب", "Parta / Ofis"),
                ("madrasa", "مَدْرَسَة", "Maktab"),
                ("mu'allim", "مُعَلِّم", "O'qituvchi"),
                ("tilmidh", "تِلْمِيذ", "O'quvchi"),
                ("sabura", "سَبُورَة", "Doska"),
                ("daftar", "دَفْتَر", "Daftar"),
                ("kursiy", "كُرْسِيّ", "Stul"),
                ("fasl", "فَصْل", "Sinf"),
            ]
        }

        total_words = 0
        new_words = 0

        for cat_name, words in dataset.items():
            # Create Category
            category, created = VocabularyCategory.objects.get_or_create(name=cat_name)
            if created:
                self.stdout.write(f"Kategoriya yaratildi: {cat_name}")

            for translit, arabic, uzbek in words:
                total_words += 1
                
                # Check exist
                if Word.objects.filter(arabic=arabic).exists():
                    self.stdout.write(f" - Mavjud: {arabic} ({uzbek})")
                    continue

                self.stdout.write(f" + Yaratilmoqda: {arabic} ({uzbek})...")

                try:
                    # Generate Audio via edge-tts (Male Voice)
                    mp3_bytes = asyncio.run(self._generate_audio(arabic, edge_tts))
                    mp3_name = f"male_{translit.replace(' ', '_')}_{int(time.time())}.mp3"
                    mp3_content = ContentFile(mp3_bytes)

                    # Create Word Object
                    word = Word(
                        arabic=arabic,
                        translation_uz=uzbek,
                        transliteration=translit,
                        category=category,
                        difficulty='easy',
                        audio_source='edge-tts-male'
                    )
                    
                    # Validate/Save
                    word.audio.save(mp3_name, mp3_content, save=True)
                    new_words += 1
                    
                    # Be nice to API
                    time.sleep(0.5) 

                except Exception as e:
                    self.stdout.write(self.style.ERROR(f"Xatolik ({arabic}): {e}"))

        self.stdout.write(self.style.SUCCESS(f"-----------------------------------"))
        self.stdout.write(self.style.SUCCESS(f"TUGADI! Jami: {total_words}, Yangi: {new_words} (ERKAK OVOZI)"))

    async def _generate_audio(self, text, edge_tts):
        """Generate audio using edge-tts with male Arabic voice"""
        communicate = edge_tts.Communicate(text, ARABIC_MALE_VOICE)
        audio_bytes = b""
        async for chunk in communicate.stream():
            if chunk["type"] == "audio":
                audio_bytes += chunk["data"]
        return audio_bytes
