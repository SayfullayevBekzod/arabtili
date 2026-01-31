"""
Management command to seed Speaking lessons from shifoviya.json
"""
import json
import os
from django.core.management.base import BaseCommand
from django.conf import settings
from arab.models import SpeakingCategory, SpeakingLesson


class Command(BaseCommand):
    help = 'Seed Speaking lessons from shifoviya.json'

    def handle(self, *args, **options):
        json_path = os.path.join(settings.BASE_DIR, 'shifoviya.json')
        
        self.stdout.write(f"Loading from: {json_path}")
        
        if not os.path.exists(json_path):
            self.stderr.write(self.style.ERROR(f"File not found: {json_path}"))
            return
        
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Create or get the main category
        category, created = SpeakingCategory.objects.get_or_create(
            name="Shifohiyya",
            defaults={
                'name_uz': "Shifohiyya - Og'zaki darslar",
                'icon': 'fas fa-book-open',
                'description': data.get('kitob_malumotlari', {}).get('nomi', 'Arabic speaking lessons'),
                'order': 1
            }
        )
        
        if created:
            self.stdout.write(self.style.SUCCESS(f"Created category: {category.name_uz}"))
        
        lessons_data = data.get('darslar', [])
        created_count = 0
        updated_count = 0
        
        for lesson_data in lessons_data:
            dars_raqami = lesson_data.get('dars_raqami', 0)
            sarlavha_ar = lesson_data.get('sarlavha_arabcha', '')
            sarlavha_uz = lesson_data.get('sarlavha_ozbekcha', f"{dars_raqami}-dars")
            
            # Build dialogue from matnlar
            matnlar = lesson_data.get('matnlar', {})
            dialogue_ar = matnlar.get('arabcha', '')
            dialogue_uz = matnlar.get('ozbekcha', '')
            
            # Build vocabulary as JSON
            lugat = lesson_data.get('lugat', [])
            key_phrases = json.dumps(lugat, ensure_ascii=False) if lugat else ''
            
            # Determine level based on lesson number
            if dars_raqami <= 10:
                level = 'beginner'
            elif dars_raqami <= 30:
                level = 'intermediate'
            else:
                level = 'advanced'
            
            lesson, created = SpeakingLesson.objects.update_or_create(
                category=category,
                lesson_number=dars_raqami,
                defaults={
                    'title': sarlavha_ar,
                    'title_uz': sarlavha_uz,
                    'level': level,
                    'dialogue_arabic': dialogue_ar,
                    'dialogue_uz': dialogue_uz,
                    'key_phrases': key_phrases,
                    'estimated_minutes': 10 + (dars_raqami % 5),
                    'xp_reward': 15 + (dars_raqami % 3) * 5,
                }
            )
            
            if created:
                created_count += 1
            else:
                updated_count += 1
        
        self.stdout.write(self.style.SUCCESS(
            f"Done! Created {created_count} lessons, updated {updated_count} lessons."
        ))
