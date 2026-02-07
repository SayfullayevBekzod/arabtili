import os
import json
from django.core.management.base import BaseCommand
from arab.models import (
    Course, Unit, Lesson, LessonSection, Word, VocabularyCategory,
    auto_generate_audio
)
from django.conf import settings
from django.db.models.signals import post_save

class Command(BaseCommand):
    help = "Seed Course, Units, Lessons, and LessonSections from shifoviya.json"

    def handle(self, *args, **options):
        # Disconnect signal to prevent auto audio generation
        post_save.disconnect(auto_generate_audio, sender=Word)
        
        json_path = os.path.join(settings.BASE_DIR, 'shifoviya.json')
        
        if not os.path.exists(json_path):
            self.stdout.write(self.style.ERROR(f"Fayl topilmadi: {json_path}"))
            return

        self.stdout.write(self.style.SUCCESS("Shifohiyya kursini yaratish boshlandi..."))
        
        try:
            with open(json_path, 'r', encoding='utf-8') as f:
                content = json.load(f)
            
            kitob_info = content.get('kitob_malumotlari', {})
            darslar = content.get('darslar', [])
            
            # 1. Create or get Course
            course, created = Course.objects.get_or_create(
                title=kitob_info.get('nomi', "Shifohiyya - 1-qism"),
                defaults={
                    'description': f"Muallif: {kitob_info.get('muallif', 'Ahmad Hodiy Maqsudiy')}\nNashr yili: {kitob_info.get('nashr_yili', '2014')}\nManba: {kitob_info.get('manba', 'www.arabic.uz')}",
                    'level': 'A1',
                    'is_published': True
                }
            )
            if created:
                self.stdout.write(f"Kurs yaratildi: {course.title}")
            else:
                self.stdout.write(f"Kurs mavjud: {course.title}")
            
            # 2. Create Units (group lessons by 10)
            lessons_per_unit = 10
            unit_count = (len(darslar) // lessons_per_unit) + (1 if len(darslar) % lessons_per_unit > 0 else 0)
            
            units = []
            for i in range(unit_count):
                unit, _ = Unit.objects.get_or_create(
                    course=course,
                    order=i + 1,
                    defaults={'title': f"Bo'lim {i + 1}"}
                )
                units.append(unit)
                self.stdout.write(f"  Bo'lim yaratildi: {unit.title}")

            # 3. Create Lessons and Sections
            lesson_count = 0
            for idx, dars in enumerate(darslar):
                unit_idx = idx // lessons_per_unit
                unit = units[unit_idx]
                
                lesson_order = (idx % lessons_per_unit) + 1
                
                lesson, created = Lesson.objects.get_or_create(
                    unit=unit,
                    order=lesson_order,
                    defaults={
                        'title': dars.get('sarlavha_ozbekcha', f'{idx+1}-dars'),
                        'theory': dars.get('sarlavha_arabcha', ''),
                        'estimated_minutes': 15
                    }
                )
                
                if created:
                    lesson_count += 1
                    
                    # Create LessonSection for Vocabulary
                    lugat = dars.get('lugat', [])
                    if lugat:
                        vocab_content = "\n".join([f"**{item.get('arabcha', '')}** - {item.get('ozbekcha', '')}" for item in lugat])
                        LessonSection.objects.create(
                            lesson=lesson,
                            title="Lug'at",
                            content=vocab_content,
                            order=1
                        )
                    
                    # Create LessonSection for Text
                    matnlar = dars.get('matnlar', {})
                    if matnlar:
                        text_content = f"**Arabcha:**\n{matnlar.get('arabcha', '')}\n\n**O'zbekcha:**\n{matnlar.get('ozbekcha', '')}"
                        LessonSection.objects.create(
                            lesson=lesson,
                            title="Matnlar",
                            content=text_content,
                            order=2
                        )
                    
                    # Link words to this lesson
                    for item in lugat:
                        arabic = item.get('arabcha')
                        if arabic:
                            Word.objects.filter(arabic=arabic).update(lesson=lesson)

                    self.stdout.write(f"    Dars yaratildi: {lesson.title}")

            self.stdout.write(self.style.SUCCESS(f"Tugadi! {lesson_count} ta dars muvaffaqiyatli yaratildi."))

        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Xatolik yuz berdi: {e}"))
        finally:
            post_save.connect(auto_generate_audio, sender=Word)
