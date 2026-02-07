import os
import requests
import json
import time
from django.core.management.base import BaseCommand
from django.core.files.base import ContentFile
from arab.models import Word, VocabularyCategory
from django.conf import settings

class Command(BaseCommand):
    help = "Import words from Quran.com with professional Qari audio"

    def add_arguments(self, parser):
        parser.add_argument('--limit', type=int, default=50, help='Number of words to import')
        parser.add_argument('--start_page', type=int, default=1, help='Start page for the API')

    def handle(self, *args, **options):
        limit = options['limit']
        start_page = options['start_page']
        
        category, _ = VocabularyCategory.objects.get_or_create(
            name='Quran',
            defaults={'description': 'Quroni Karimda kelgan so\'zlar (Professional talaffuz)'}
        )
        
        # 1. Clear existing words to remove glyphs (harflar)
        self.stdout.write(self.style.WARNING("Eski Quran turidagi so'zlar o'chirilmoqda..."))
        Word.objects.filter(category=category).delete()
        
        count = 0
        page = start_page
        
        self.stdout.write(self.style.SUCCESS(f"Quran.com dan {limit} ta haqiqiy so'z yuklanmoqda..."))
        
        # Enhanced manual mapping for Fatiha and common words
        MANUAL_MAPPING = {
            "In (the) name": "Nomi bilan",
            "(of) Allah": "Allohning",
            "the Most Gracious": "Rahmon",
            "the Most Merciful": "Rahim",
            "All praises": "Hamdlar",
            "(be) to Allah": "Allohga",
            "the Lord": "Robb",
            "(of) the worlds": "Olamlarning",
            "The Most Gracious": "Rahmon",
            "The Most Merciful": "Rahim",
            "(The) Master": "Ega (Podshoh)",
            "(of) the Day": "Kunining",
            "(of) Judgment": "Qiyomat",
            "You Alone": "Faqat Sengagina",
            "we worship": "ibodat qilamiz",
            "and You Alone": "va Faqat Sendangina",
            "we ask for help": "yordam so'raymiz",
            "Guide us": "Bizni boshla",
            "(to) the path": "yo'lga",
            "the straight": "to'g'ri",
            "(The) path": "Yo'liga",
            "(of) those": "shundaylarningki",
            "You have bestowed Favor": "Sen ne'mat bergansan",
            "on them": "ularga",
            "not": "emas",
            "(of) those who earned (Your) wrath": "g'azabga uchraganlarning",
            "and not": "va yo'q",
            "(of) those who go astray": "yo'ldan ozganlarning",
            "Alif Lam Mim": "Alif Lom Mim",
            "This": "Bu",
            "(is) the Book": "(shunday) kitobki",
            "no": "yo'q",
            "doubt": "shubha",
            "in it": "unda (uning haq ekanligida)",
            "(it is) a guidance": "hidoyatdir",
            "for the God-fearing": "taqvodorlar uchun",
            "Those who": "Ular shundayki",
            "believe": "iymon keltiradilar",
            "in the unseen": "g'aybga",
            "and establish": "va barpo qiladilar",
            "the prayer": "namozni",
            "and from what": "va Biz rizq qilib bergan narsalardan",
            "We have provided them": "Biz ularga",
            "they spend": "infoq qiladilar",
        }

        while count < limit:
            # API URL with explicit text_uthmani field
            url = f"https://api.quran.com/api/v4/verses/by_page/{page}?words=true&word_fields=text_uthmani,transliteration&word_translation_language=en"
            
            try:
                response = requests.get(url, timeout=15)
                data = response.json()
                
                verses = data.get('verses', [])
                if not verses:
                    break
                
                for verse in verses:
                    words = verse.get('words', [])
                    for w_data in words:
                        if count >= limit:
                            break
                        
                        char_type = w_data.get('char_type_name')
                        if char_type != 'word':
                            continue
                            
                        # Use text_uthmani for actual Arabic text instead of font glyph
                        arabic_text = w_data.get('text_uthmani') or w_data.get('text')
                        if not arabic_text:
                            continue
                            
                        # Avoid duplicates
                        if Word.objects.filter(arabic=arabic_text).exists():
                            continue
                            
                        en_translation = w_data.get('translation', {}).get('text', '')
                        transliteration = w_data.get('transliteration', {}).get('text', '')
                        audio_url_partial = w_data.get('audio_url')
                        
                        if not audio_url_partial:
                            continue
                            
                        # Full audio URL from CDN
                        full_audio_url = f"https://audio.qurancdn.com/{audio_url_partial}"
                        
                        # Translate
                        uz_translation = MANUAL_MAPPING.get(en_translation, f"{en_translation}")
                        
                        self.stdout.write(f"Yuklanmoqda: {arabic_text} ({en_translation})...", ending="")
                        
                        try:
                            # Create Word object
                            word_obj = Word(
                                arabic=arabic_text,
                                transliteration=transliteration,
                                translation_uz=uz_translation,
                                translation_ru="",
                                category=category,
                                audio_source="quran_com",
                                is_verified=True
                            )
                            
                            # Download Audio
                            audio_resp = requests.get(full_audio_url, timeout=10)
                            if audio_resp.status_code == 200:
                                filename = f"quran_{count}_{int(time.time())}.mp3"
                                word_obj.audio.save(filename, ContentFile(audio_resp.content), save=False)
                            
                            word_obj.save()
                            self.stdout.write(self.style.SUCCESS(" ✓"))
                            count += 1
                            
                        except Exception as inner_e:
                            self.stdout.write(self.style.ERROR(f" ✗ ({inner_e})"))
                
                page += 1
                if page > 604:
                    break
                    
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"Xatolik yuz berdi: {e}"))
                break

        self.stdout.write(self.style.SUCCESS(f"Tugadi! {count} ta haqiqiy so'z muvaffaqiyatli import qilindi."))
