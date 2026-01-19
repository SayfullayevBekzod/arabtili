from django.contrib.auth import get_user_model
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone
from .models import Letter, UserCard

User = get_user_model()

@receiver(post_save, sender=User)
def create_letter_cards(sender, instance, created, **kwargs):
    if not created:
        return
    now = timezone.now()
    letters = Letter.objects.all()
    for l in letters:
        UserCard.objects.get_or_create(user=instance, letter=l, defaults={"due_at": now})
