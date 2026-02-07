
import os
import json
from django.core.management.base import BaseCommand
from django.conf import settings
from django.db.models.signals import post_save
from arab.models import Course, Unit, Lesson, LessonSection, Word, VocabularyCategory, WordExample, auto_generate_audio

class Command(BaseCommand):
    help = "Seed lessons and vocabulary from shifoviya.json"

    def handle(self, *args, **options):
        # Disconnect signal to prevent auto audio generation and DB locks
        post_save.disconnect(auto_generate_audio, sender=Word)

        json_path = os.path.join(settings.BASE_DIR, 'shifoviya.json')
        
        if not os.path.exists(json_path):
            self.stdout.write(self.style.ERROR(f"Fav qutilmadi: {json_path}"))
            return

        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        # 1. Create Course
        course_title = data['kitob_malumotlari']['nomi']
        course, created = Course.objects.get_or_create(
            title=course_title,
            defaults={
                'description': f"Muallif: {data['kitob_malumotlari']['muallif']}. Nashr yili: {data['kitob_malumotlari']['nashr_yili']}",
                'level': 'A1',
                'is_published': True
            }
        )
        if created:
            self.stdout.write(self.style.SUCCESS(f"Kurs yaratildi: {course.title}"))
        else:
            self.stdout.write(f"Kurs mavjud: {course.title}")

        # 2. Create Unit (Assuming 1 unit for this part)
        unit, created = Unit.objects.update_or_create(
            course=course,
            order=1,
            defaults={'title': "1-qism"}
        )

        darslar = data.get('darslar', [])
        
        for dars in darslar:
            lesson_num = dars.get('dars_raqami')
            title_uz = dars.get('sarlavha_ozbekcha')
            title_ar = dars.get('sarlavha_arabcha')
            
            # 3. Create Lesson
            lesson, created = Lesson.objects.update_or_create(
                unit=unit,
                order=lesson_num,
                defaults={
                    'title': title_uz,
                    'theory': title_ar, # Storing Arabic title in theory for now or description
                    'estimated_minutes': 15
                }
            )
            
            if created:
                 self.stdout.write(f"  + Dars yaratildi: {lesson.title}")

            # 4. Create Lesson Content (Text)
            matnlar = dars.get('matnlar', {})
            if matnlar:
                content_md = f"**Arabcha:**\n\n{matnlar.get('arabcha', '')}\n\n**O'zbekcha:**\n\n{matnlar.get('ozbekcha', '')}"
                
                LessonSection.objects.update_or_create(
                    lesson=lesson,
                    order=1,
                    defaults={
                        'title': "Dars Matni",
                        'content': content_md,
                    }
                )

            # 5. Process Vocabulary
            lugat = dars.get('lugat', [])
            
            # Category for this lesson
            cat_name = f"Shifohiyya - {lesson_num}-dars"
            category, _ = VocabularyCategory.objects.get_or_create(name=cat_name, defaults={'description': title_uz})

            for word_item in lugat:
                arabic = word_item.get('arabcha')
                uzbek = word_item.get('ozbekcha')
                
                if not arabic:
                    continue

                # Create/Get Word
                word, created = Word.objects.update_or_create(
                    arabic=arabic,
                    defaults={
                        'translation_uz': uzbek,
                        'category': category,
                        'source_name': 'Shifohiyya',
                        'is_verified': True,
                        'lesson': lesson # Link strictly to this lesson
                    }
                )
                
                if not created:
                    # If exists, maybe update lesson if it has none?
                    if not word.lesson:
                        word.lesson = lesson
                        word.save()

        self.stdout.write(self.style.SUCCESS(f"Muvaffaqiyatli yakunlandi! {len(darslar)} ta dars qayta ishlandi."))
