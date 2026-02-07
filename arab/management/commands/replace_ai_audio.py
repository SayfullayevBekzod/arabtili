import os
import requests
import time
from django.core.management.base import BaseCommand
from django.core.files.base import ContentFile
from arab.models import Word

class Command(BaseCommand):
    help = "Replace AI-generated audio with professional Qori recordings from Quran.com"

    def add_arguments(self, parser):
        parser.add_argument('--force', action='store_true', help='Force replace even if it has non-auto source')
        parser.add_argument('--limit', type=int, default=100, help='Limit number of words to process')

    def handle(self, *args, **options):
        force = options['force']
        limit = options['limit']

        # Filter words with AI audio or generic 'auto' source
        if force:
            words = Word.objects.all()
        else:
            words = Word.objects.filter(audio_source__in=['auto', 'edge-tts', ''])
        
        words = words.exclude(arabic='')[:limit]
        total = words.count()
        
        if total == 0:
            self.stdout.write(self.style.SUCCESS("Almashtirilishi kerak bo'lgan so'zlar topilmadi."))
            return

        self.stdout.write(self.style.MIGRATE_HEADING(f"Jami {total} ta so'zni qayta ishlash boshlandi..."))
        
        success_count = 0
        skip_count = 0
        error_count = 0

        for i, word in enumerate(words, 1):
            arabic_clean = word.arabic.strip().strip('،,.;:!?')
            
            if len(arabic_clean) < 2:
                self.stdout.write(f"[{i}/{total}] {word.arabic} (Siz juda qisqa - skip)")
                skip_count += 1
                continue

            self.stdout.write(f"[{i}/{total}] {arabic_clean}...", ending="")
            
            try:
                # 1. Search Quran.com API
                search_url = f"https://api.quran.com/api/v4/search?q={arabic_clean}&size=1&language=uz"
                search_resp = requests.get(search_url, timeout=10)
                if search_resp.status_code == 200:
                    search_data = search_resp.json()
                    results = search_data.get('search', {}).get('results', [])
                    
                    if results:
                        verse_key = results[0].get('verse_key')
                        verse_url = f"https://api.quran.com/api/v4/verses/by_key/{verse_key}?words=true&word_fields=text_uthmani,audio_url"
                        verse_resp = requests.get(verse_url, timeout=10)
                        
                        if verse_resp.status_code == 200:
                            words_list = verse_resp.json().get('verse', {}).get('words', [])
                            target_audio_url = None
                            
                            import re
                            def norm(t):
                                if not t: return ""
                                t = re.sub(r'[\u064B-\u0652]', '', t)
                                t = re.sub(r'[آأإٱءؤئ]', 'ا', t)
                                t = re.sub(r'[ى]', 'ا', t)
                                t = re.sub(r'[\u0670\u06E5\u06E6]', '', t)
                                t = re.sub(r'ـ', '', t)
                                t = re.sub(r'ا+', 'ا', t)
                                return t.strip()
                            
                            target_norm = norm(arabic_clean)
                            for w in words_list:
                                w_text = w.get('text_uthmani') or w.get('text', '')
                                if w_text == arabic_clean or (norm(w_text) == target_norm and target_norm):
                                    target_audio_url = w.get('audio_url')
                                    break
                            
                            if target_audio_url:
                                full_url = f"https://audio.qurancdn.com/{target_audio_url}"
                                audio_content = requests.get(full_url, timeout=10).content
                                
                                filename = f"qori_{word.pk}_{int(time.time())}.mp3"
                                word.audio.save(filename, ContentFile(audio_content), save=False)
                                word.audio_source = "qori_quran_com"
                                word.is_verified = True
                                word.save()
                                
                                self.stdout.write(self.style.SUCCESS(" ✓ Professional audio almashtirildi"))
                                success_count += 1
                                continue

                self.stdout.write(self.style.WARNING(" Topilmadi (skip)"))
                skip_count += 1
                
            except Exception as e:
                self.stdout.write(self.style.ERROR(f" Xato: {e}"))
                error_count += 1
                self.stdout.write(self.style.ERROR(f" Xato: {e}"))
                error_count += 1
            
            # Rate limiting
            time.sleep(0.5)

        self.stdout.write("-" * 50)
        self.stdout.write(self.style.SUCCESS(f"Tugadi! Muvaffaqiyatli: {success_count}, Topilmadi: {skip_count}, Xato: {error_count}"))
