from django.core.management.base import BaseCommand
from django.core.management import call_command
import sys

class Command(BaseCommand):
    help = 'Runs all seed commands to populate the database'

    def handle(self, *args, **kwargs):
        self.stdout.write(self.style.WARNING('🚀 Starting Full Database Seeding...'))

        commands = [
            # Core Data
            'init_data',
            
            # Content
            'seed_alphabet',
            'import_new_words',
            
            # Tajweed Pro
            'seed_tajweed_pro',
            'seed_tajweed_quiz',
            
            # Additional content can be added here once commands are created
        ]

        for cmd in commands:
            try:
                self.stdout.write(self.style.SUCCESS(f'📦 Running {cmd}...'))
                call_command(cmd)
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'❌ Failed to run {cmd}: {str(e)}'))
                # We don't exit here, we try to continue with other seeds
                
        self.stdout.write(self.style.SUCCESS('✅ All seed commands finished!'))
