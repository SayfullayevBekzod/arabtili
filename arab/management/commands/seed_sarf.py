
import os
import re
import pypdf
from django.core.management.base import BaseCommand
from django.conf import settings
from django.db.models.signals import post_save
from arab.models import Course, Unit, Lesson, LessonSection, Word, VocabularyCategory, auto_generate_audio

class Command(BaseCommand):
    help = "Seed lessons and vocabulary from Mukammal Sarf PDF"

    def handle(self, *args, **options):
        # Disconnect signal
        post_save.disconnect(auto_generate_audio, sender=Word)

        pdf_path = os.path.join(settings.BASE_DIR, 'mukammal-sarf-darsligi.pdf')

        if not os.path.exists(pdf_path):
            self.stdout.write(self.style.ERROR(f"Fayl topilmadi: {pdf_path}"))
            return

        # 1. Create Course
        course, _ = Course.objects.get_or_create(
            title="Mukammal Sarf",
            defaults={
                'description': "Arab tili sarf fani bo'yicha mukammal darslik.",
                'level': 'A2',
                'is_published': True
            }
        )

        # 2. Create Unit
        unit, _ = Unit.objects.update_or_create(
            course=course,
            order=1,
            defaults={'title': "Asosiy qism"}
        )
        
        # Category for vocab
        category, _ = VocabularyCategory.objects.get_or_create(name="Mukammal Sarf So'zlari")

        # 0. Clear existing lessons to remove empty ones from previous bad runs
        self.stdout.write("Eski darslarni o'chirmoqda...")
        Lesson.objects.filter(unit__course=course).delete()

        lesson_count = 0
        try:
            reader = pypdf.PdfReader(pdf_path)
            # Extract all text first
            full_text = ""
            for i in range(len(reader.pages)):
                page = reader.pages[i]
                full_text += page.extract_text() + "\n"

            # Regex for headers like "1. Ism", "2. Fe'l"
            # Pattern: newline, number, dot, space, text
            # We use capturing group to keep the delimiter
            pattern = r'(\n\d+\.\s+[^\n]+)'
            parts = re.split(pattern, full_text)

            # parts[0] is intro before first header
            # parts[1] is header1, parts[2] is content1, parts[3] is header2...
            
            # Create Intro lesson
            if len(parts[0].strip()) > 50:
                lesson_count += 1
                Lesson.objects.update_or_create(
                    unit=unit,
                    order=lesson_count,
                    defaults={
                        'title': "Kirish (Muqaddima)",
                        'theory': "Darslikka kirish qismi.",
                        'estimated_minutes': 10
                    }
                )
                LessonSection.objects.update_or_create(
                    lesson=Lesson.objects.get(unit=unit, order=lesson_count),
                    order=1,
                    defaults={'title': "Matn", 'content': parts[0].strip()}
                )

            # Process sections
            current_header = ""
            for i in range(1, len(parts), 2):
                header = parts[i].strip()
                content = parts[i+1].strip() if i+1 < len(parts) else ""
                
                # Skip if content is too short (likely TOC or just precise header without text)
                if len(content) < 50:
                    continue

                lesson_count += 1
                # Clean header (remove newline)
                title = header.replace('\n', '')
                if len(title) > 100: title = title[:97] + "..."

                lesson, _ = Lesson.objects.update_or_create(
                    unit=unit,
                    order=lesson_count,
                    defaults={
                        'title': title,
                        'estimated_minutes': 15
                    }
                )
                
                LessonSection.objects.update_or_create(
                    lesson=lesson,
                    order=1,
                    defaults={
                        'title': "Qoida",
                        'content': content
                    }
                )
                
                self.stdout.write(f"  + {title} yaratildi ({len(content)} belgilar).")
                
                # Extract Arabic words from this section
                arabic_words = re.findall(r'[\u0600-\u06FF]+', content)
                for ar_word in arabic_words:
                    if len(ar_word) > 1:
                         Word.objects.update_or_create(
                            arabic=ar_word,
                            defaults={
                                'source_name': 'Mukammal Sarf',
                                'category': category,
                                'is_verified': False,
                                'lesson': lesson
                            }
                        )

            self.stdout.write(self.style.SUCCESS(f"Tugadi! {lesson_count} ta dars (mavzu) yaratildi."))

        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Xatolik: {e}"))
