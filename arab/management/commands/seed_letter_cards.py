from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.utils import timezone

from arab.models import Letter, UserCard

class Command(BaseCommand):
    help = "Existing userlar uchun Letter UserCard yaratadi"

    def handle(self, *args, **opts):
        User = get_user_model()
        now = timezone.now()
        letters = list(Letter.objects.all())
        users = list(User.objects.all())

        created = 0
        for u in users:
            for l in letters:
                _, is_created = UserCard.objects.get_or_create(user=u, letter=l, defaults={"due_at": now})
                if is_created:
                    created += 1

        self.stdout.write(self.style.SUCCESS(f"✅ created {created} cards"))
