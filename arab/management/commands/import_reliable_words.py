import os
import json
from django.core.management.base import BaseCommand
from arab.models import Word, VocabularyCategory, WordExample, UserWordProgress, UserCard, UserFavoriteWord, auto_generate_audio
from django.conf import settings
from django.db import connection
from django.db.models.signals import post_save

class Command(BaseCommand):
    help = "Import reliable words from shifoviya.json (Shifohiyya) and remove all audio"

    def handle(self, *args, **options):
        # Disconnect signal to prevent auto audio generation
        post_save.disconnect(auto_generate_audio, sender=Word)
        
        json_path = os.path.join(settings.BASE_DIR, 'shifoviya.json')
        
        if not os.path.exists(json_path):
            self.stdout.write(self.style.ERROR(f"Fayl topilmadi: {json_path}"))
            return

        # 1. Clear existing data
        self.stdout.write(self.style.WARNING("Eski ma'lumotlar o'chirilmoqda..."))
        
        with connection.cursor() as cursor:
            cursor.execute('PRAGMA foreign_keys=OFF')
            UserFavoriteWord.objects.all().delete()
            UserCard.objects.all().delete()
            UserWordProgress.objects.all().delete()
            WordExample.objects.all().delete()
            Word.objects.all().delete()
            cursor.execute('PRAGMA foreign_keys=ON')

        # 2. Delete old audio files from media
        audio_dir = os.path.join(settings.MEDIA_ROOT, 'audio', 'words')
        if os.path.exists(audio_dir):
            self.stdout.write(f"Audio fayllar tozalanmoqda: {audio_dir}...")
            for f in os.listdir(audio_dir):
                file_path = os.path.join(audio_dir, f)
                try:
                    if os.path.isfile(file_path):
                        os.unlink(file_path)
                except Exception as e:
                    self.stdout.write(f"Faylni o'chirishda xato {f}: {e}")

        # 3. Import new data from shifoviya.json
        self.stdout.write(self.style.SUCCESS("Shifoxiyya (Ahmad Hodiy Maqsudiy) manbasidan so'zlar import qilinmoqda..."))
        
        try:
            with open(json_path, 'r', encoding='utf-8') as f:
                content = json.load(f)
            
            darslar = content.get('darslar', [])
            count = 0
            category_cache = {}

            for dars in darslar:
                cat_name = dars.get('sarlavha_ozbekcha', 'General')
                lugat = dars.get('lugat', [])
                
                if cat_name not in category_cache:
                    category, _ = VocabularyCategory.objects.get_or_create(
                        name=cat_name,
                        defaults={'description': dars.get('sarlavha_arabcha', '')}
                    )
                    category_cache[cat_name] = category
                
                category = category_cache[cat_name]

                for item in lugat:
                    arabic = item.get('arabcha')
                    uz = item.get('ozbekcha')

                    if not arabic or not uz:
                        continue

                    # Avoid duplicates in the same import
                    if Word.objects.filter(arabic=arabic).exists():
                        continue

                    # Create Word
                    Word.objects.create(
                        arabic=arabic,
                        transliteration="", # Will be empty for now as shifoviya doesn't have it for every word
                        translation_uz=uz,
                        translation_ru="",
                        category=category,
                        audio=None,
                        audio_source="shifohiyya",
                        is_verified=True
                    )
                    
                    count += 1
                    if count % 50 == 0:
                        self.stdout.write(f"Import qilindi: {count} ta so'z...")

            self.stdout.write(self.style.SUCCESS(f"Tugadi! {count} ta ishonchli so'z muvaffaqiyatli import qilindi."))

        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Xatolik yuz berdi: {e}"))
        finally:
            # Re-connect signal just in case (though management command ends here)
            post_save.connect(auto_generate_audio, sender=Word)
