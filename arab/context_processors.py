from .models import UserGamification, DailyQuest, UserQuestProgress
from django.utils import timezone
import random

def gamification_context(request):
    if request.user.is_authenticated:
        game, _ = UserGamification.objects.get_or_create(user=request.user)
        
        # Check Daily Quests (Lazy loading)
        today = timezone.now().date()
        user_quests = UserQuestProgress.objects.filter(user=request.user, day=today)
        
        if not user_quests.exists():
            # Assign random quests (e.g., 3)
            all_quests = list(DailyQuest.objects.all())
            if all_quests:
                selected = random.sample(all_quests, min(len(all_quests), 3))
                for q in selected:
                    UserQuestProgress.objects.create(user=request.user, quest=q, day=today)
                user_quests = UserQuestProgress.objects.filter(user=request.user, day=today)

        return {
            'game': game,
            'daily_quests': user_quests
        }
    return {}
