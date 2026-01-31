from django.core.management.base import BaseCommand
from django.core.management import call_command
import sys

class Command(BaseCommand):
    help = 'Runs all seed commands to populate the database'

    def handle(self, *args, **kwargs):
        self.stdout.write(self.style.WARNING('🚀 Starting Full Database Seeding...'))

        commands = [
            # 1. Core Data (Categories, Courses, Levels)
            'init_data',
            
            # 2. Alphabet & Letters
            'seed_alphabet',
            'seed_letter_cards',
            
            # 3. Vocabulary
            'seed_words',
            'import_new_words',
            
            # 4. Grammar & Verbs
            'seed_verbs',
            
            # 5. Speaking (Shifoviya)
            'seed_speaking',
            
            # 6. Tajweed (Rules & Quiz)
            'seed_tajweed',
            'seed_tajweed_tags',
            'seed_tajweed_examples',
            'seed_tajweed_pro',
            'seed_tajweed_quiz',
            
            # 7. Conversational Scenarios
            'seed_scenarios',
            
            # 8. Placement Test
            'seed_placement',
        ]

        for cmd in commands:
            try:
                self.stdout.write(self.style.SUCCESS(f'📦 Running {cmd}...'))
                call_command(cmd)
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'❌ Failed to run {cmd}: {str(e)}'))
                # We don't exit here, we try to continue with other seeds
                
        self.stdout.write(self.style.SUCCESS('✅ All seed commands finished!'))
