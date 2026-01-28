from .models import UserGamification, Mission, UserMissionProgress, UserDailyStat
from django.utils import timezone
import random

def gamification_context(request):
    if request.user.is_authenticated:
        game, _ = UserGamification.objects.get_or_create(user=request.user)
        
        # Heart Refill Logic (1 heart every 3 hours, max 5)
        now = timezone.now()
        if game.hearts < 5:
            delta = now - game.last_heart_refill
            hours_passed = delta.total_seconds() // 3600
            refill_amount = int(hours_passed // 3)  # 1 heart per 3 hours
            
            if refill_amount > 0:
                game.hearts = min(5, game.hearts + refill_amount)
                # Keep the remainder of time
                seconds_consumed = refill_amount * 3 * 3600
                game.last_heart_refill = game.last_heart_refill + timezone.timedelta(seconds=seconds_consumed)
                game.save(update_fields=['hearts', 'last_heart_refill'])
        else:
            # If hearts are full, keep last_heart_refill updated to now to avoid immediate refill later
            game.last_heart_refill = now
            game.save(update_fields=['last_heart_refill'])

        # Check Mission Progress (Lazy loading)
        today = now.date()
        user_missions = UserMissionProgress.objects.filter(user=request.user, date=today).select_related("mission")
        
        if user_missions.count() < 3:
            # If no Mission templates exist, create some defaults
            if Mission.objects.count() == 0:
                Mission.objects.create(title="Review 10 ta so'z", mission_type="review", required_count=10, xp_reward=15)
                Mission.objects.create(title="1 ta dars tugat", mission_type="lesson", required_count=1, xp_reward=50)
                Mission.objects.create(title="15 daqiqa shug'ullan", mission_type="time", required_count=15, xp_reward=30)

            # Assign random missions
            all_missions = list(Mission.objects.filter(is_active=True))
            if all_missions:
                # Pick unique missions for today
                existing_mission_ids = user_missions.values_list('mission_id', flat=True)
                available = [m for m in all_missions if m.id not in existing_mission_ids]
                
                needed = 3 - user_missions.count()
                if available:
                    selected = random.sample(available, min(len(available), needed))
                    
                    # Current stats for syncing
                    stat = UserDailyStat.objects.filter(user=request.user, day=today).first()
                    
                    for m in selected:
                        current = 0
                        if stat:
                            if m.mission_type == "review": current = stat.reviews_done
                            elif m.mission_type == "lesson": current = stat.lessons_done
                            elif m.mission_type == "word": current = stat.new_words
                            elif m.mission_type == "time": current = stat.study_minutes
                        
                        is_done = current >= m.required_count
                        UserMissionProgress.objects.create(
                            user=request.user,
                            mission=m,
                            date=today,
                            current_progress=min(current, m.required_count),
                            is_completed=is_done
                        )
                        if is_done:
                            game.xp_total += m.xp_reward
                            game.save(update_fields=['xp_total'])
                    
                    user_missions = UserMissionProgress.objects.filter(user=request.user, date=today).select_related("mission")

        # Calculate progress percent for UI
        for um in user_missions:
            um.progress_percent = int((um.current_progress / um.mission.required_count) * 100) if um.mission.required_count > 0 else 0

        return {
            'game': game,
            'daily_quests': user_missions # Keep key as daily_quests for template compatibility
        }
    return {}
