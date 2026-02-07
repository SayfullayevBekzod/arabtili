import os
import json
from django.core.management.base import BaseCommand
from arab.models import Word, WordExample, auto_generate_audio
from django.conf import settings
from django.db.models.signals import post_save

class Command(BaseCommand):
    help = "Seed WordExamples from shifoviya.json"

    def handle(self, *args, **options):
        # Disconnect signal just in case, though we are not creating words
        post_save.disconnect(auto_generate_audio, sender=Word)
        
        json_path = os.path.join(settings.BASE_DIR, 'shifoviya.json')
        
        if not os.path.exists(json_path):
            self.stdout.write(self.style.ERROR(f"Fayl topilmadi: {json_path}"))
            return

        self.stdout.write(self.style.SUCCESS("Shifohiyya gaplarini lug'at uchun import qilish boshlandi..."))
        
        try:
            with open(json_path, 'r', encoding='utf-8') as f:
                content = json.load(f)
            
            darslar = content.get('darslar', [])
            example_count = 0
            
            for dars in darslar:
                matnlar = dars.get('matnlar', {})
                arab_text = matnlar.get('arabcha', '')
                uz_text = matnlar.get('ozbekcha', '')
                
                if not arab_text or not uz_text:
                    continue
                
                # Split Arabic by *
                arab_sentences = [s.strip() for s in arab_text.split('*') if s.strip()]
                
                # Split Uzbek by * or .
                if '*' in uz_text:
                    uz_sentences = [s.strip() for s in uz_text.split('*') if s.strip()]
                else:
                    # heuristic splitting by dot
                    # This might be imperfect if there are dots in abbreviations, but mostly fine here
                    uz_sentences = [s.strip() for s in uz_text.replace('Mr.', 'Mr').replace('..', '.').split('.') if s.strip()]

                # Debug if mismatch is huge
                if abs(len(arab_sentences) - len(uz_sentences)) > 2:
                     print(f"Warning: Sentence count mismatch for lesson. Arab: {len(arab_sentences)}, Uz: {len(uz_sentences)}")
                
                # Try to pair them
                for i in range(min(len(arab_sentences), len(uz_sentences))):
                    a_sent = arab_sentences[i]
                    u_sent = uz_sentences[i]
                    
                    # Find which words from the vocabulary appear in this sentence
                    # This is a bit tricky due to harakatlar and partial matches
                    # We'll look for words that were imported and are in the same lesson
                    
                    # For now, let's just find ALL words that appear in this sentence
                    # to make it useful across the dictionary
                    
                    for word in Word.objects.all():
                        # We use simple inclusion for now, might need better matching for Arabic
                        if word.arabic in a_sent:
                            # Create example only if it doesn't exist for this word
                            if not WordExample.objects.filter(word=word, arabic_text=a_sent).exists():
                                WordExample.objects.create(
                                    word=word,
                                    arabic_text=a_sent,
                                    translation_uz=u_sent
                                )
                                example_count += 1
                
                if example_count % 100 == 0 and example_count > 0:
                    self.stdout.write(f"  {example_count} ta misol qo'shildi...")

            self.stdout.write(self.style.SUCCESS(f"Tugadi! {example_count} ta misol muvaffaqiyatli qo'shildi."))

        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Xatolik yuz berdi: {e}"))
        finally:
            post_save.connect(auto_generate_audio, sender=Word)
