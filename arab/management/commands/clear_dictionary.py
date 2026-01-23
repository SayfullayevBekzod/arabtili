
from django.core.management.base import BaseCommand
from arab.models import Word, VocabularyCategory

class Command(BaseCommand):
    help = 'Clears all words and categories from the dictionary'

    def handle(self, *args, **kwargs):
        word_count = Word.objects.count()
        cat_count = VocabularyCategory.objects.count()
        
        Word.objects.all().delete()
        VocabularyCategory.objects.all().delete()
        
        self.stdout.write(self.style.SUCCESS(f'Successfully deleted {word_count} words and {cat_count} categories.'))
