from datetime import timedelta
import random

from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db import transaction
from django.db.models import Q, Sum
from django.shortcuts import get_object_or_404, redirect, render
from django.http import JsonResponse
from django.utils import timezone
from django.views.decorators.http import require_http_methods, require_POST



import base64
import json
import io

try:
    from PIL import Image
except ImportError:
    Image = None

from .forms import LoginForm, RegisterForm, UserUpdateForm, ProfileUpdateForm, ReminderUpdateForm
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth import update_session_auth_hash
from django.contrib import messages
from .models import (
    Course,
    Exercise,
    Lesson,
    LessonVideo,
    Letter,
    Profile,
    TajweedExample,
    TajweedQuiz,
    TajweedQuizOption,
    TajweedQuizAttempt,
    TajweedRule,
    UserCard,
    UserLessonProgress,
    UserQuizAttempt,
    UserStreak,
    UserWordProgress,
    UserVideoProgress,
    Word,
    UserDailyStat,
    UserGamification,
    UserWeakArea,
    UserReminder,
    QuranSurah,
    QuranAyah,
    Mission,
    UserMissionProgress,
    PlacementQuestion,
    PlacementOption,
    ScenarioCategory,
    Scenario,
    DialogLine,
    PhrasebookEntry,
    UserFeedback
)
from .forms import (
    RegisterForm, LoginForm, UserUpdateForm, ProfileUpdateForm, ReminderUpdateForm, FeedbackForm
)
from .progress_tracking import xp_for_next_level


def _calc_streak(user) -> dict:
    """
    daily_stats asosida streak hisoblaydi (10 review / 1 lesson / 5 yangi so‘z).
    """
    stats = UserDailyStat.objects.filter(user=user).order_by("-day")
    if not stats.exists():
        return {"current_streak": 0, "best_streak": 0}

    stats_map = {s.day: s for s in stats}
    
    def check_goal(d):
        s = stats_map.get(d)
        if not s: return False
        # Goal: 10 reviews OR 1 lesson OR 5 new words OR 15 min study
        return ((s.reviews_done or 0) >= 10) or ((s.lessons_done or 0) >= 1) or ((s.new_words or 0) >= 5) or ((s.study_minutes or 0) >= 15)

    # current streak
    today = timezone.localdate()
    cur = 0
    d = today
    # If today is not done yet, don't break streak if yesterday was active
    if not check_goal(d):
        d = d - timedelta(days=1)
    
    while check_goal(d):
        cur += 1
        d = d - timedelta(days=1)

    # best streak
    best = 0
    sorted_days = sorted([day for day in stats_map.keys() if check_goal(day)])
    run = 0
    prev = None
    for d in sorted_days:
        if prev is None or (d - prev).days == 1:
            run += 1
        else:
            best = max(best, run)
            run = 1
        prev = d
    best = max(best, run)
    
    # Save to DB (Legacy UserStreak)
    UserStreak.objects.update_or_create(
        user=user, 
        defaults={"current_streak": cur, "best_streak": best}
    )

    # Sync with UserGamification (New System)
    g, _ = UserGamification.objects.get_or_create(user=user)
    g.current_streak = cur
    if best > g.longest_streak:
        g.longest_streak = best
    g.save(update_fields=['current_streak', 'longest_streak'])

    return {"current_streak": cur, "best_streak": best}


def _update_daily_stat(user, review_inc=0, lesson_inc=0, new_word_inc=0, minutes_inc=0):
    day = timezone.localdate()
    stat, _ = UserDailyStat.objects.get_or_create(user=user, day=day)
    stat.reviews_done += review_inc
    stat.lessons_done += lesson_inc
    stat.new_words += new_word_inc
    stat.study_minutes += minutes_inc
    stat.save()
    
    # Update streak immediately
    _calc_streak(user)
    
    # Check achievements
    _check_achievements(user, stat)

    # Check Missions
    _update_daily_mission_progress(user, review_inc, lesson_inc, new_word_inc, minutes_inc)


def _update_daily_mission_progress(user, review_inc=0, lesson_inc=0, new_word_inc=0, minutes_inc=0):
    """
    Update active missions based on activity increments.
    """
    today = timezone.localdate()
    missions = UserMissionProgress.objects.filter(user=user, date=today, is_completed=False).select_related("mission")
    
    for mp in missions:
        m = mp.mission
        inc = 0
        if m.mission_type == "review": inc = review_inc
        elif m.mission_type == "lesson": inc = lesson_inc
        elif m.mission_type == "word": inc = new_word_inc
        elif m.mission_type == "time": inc = minutes_inc
        
        if inc > 0:
            mp.current_progress += inc
            # Cap at required (aesthetic, but we can store true value if needed)
            if mp.current_progress >= m.required_count:
                mp.current_progress = m.required_count
                mp.is_completed = True
                
                # Award XP
                g, _ = UserGamification.objects.get_or_create(user=user)
                g.xp_total += m.xp_reward
                g.save()
            
            mp.save()


def _get_daily_missions(user):
    """
    Returns list of daily quests/missions for the user.
    """
    try:
        from .models import UserQuestProgress
        today = timezone.localdate()
        return UserQuestProgress.objects.filter(user=user, day=today).select_related('quest')
    except Exception:
        return []


def xp_for_next_level(level):
    """
    K keyingi levelga o'tish uchun kerakli XP (oddiy formula).
    Masalan: Level * 100
    """
    return level * 100


def _check_achievements(user, stat=None):
    # Retrieve current progress
    streak_obj = UserStreak.objects.filter(user=user).first()
    cur_streak = streak_obj.current_streak if streak_obj else 0
    
    learned_words = UserDailyStat.objects.filter(user=user).aggregate(s=Sum("new_words"))["s"] or 0
    lessons_completed = UserDailyStat.objects.filter(user=user).aggregate(s=Sum("lessons_done"))["s"] or 0
    
    g, _ = UserGamification.objects.get_or_create(user=user)
    xp = g.xp_total
    
    # Define badges logic
    # Format: (id, icon, title, condition_func)
    badges_def = [
        ("streak_3", "🔥", "3 kunlik streak", lambda: cur_streak >= 3),
        ("streak_7", "🔥", "7 kunlik streak", lambda: cur_streak >= 7),
        ("streak_30", "🔥", "30 kunlik streak", lambda: cur_streak >= 30),
        
        ("words_50", "📚", "50 ta so‘z", lambda: learned_words >= 50),
        ("words_100", "📚", "100 ta so‘z", lambda: learned_words >= 100),
        ("words_500", "📚", "500 ta so‘z", lambda: learned_words >= 500),
        
        ("lessons_10", "🎓", "10 ta dars", lambda: lessons_completed >= 10),
        ("lessons_30", "🎓", "30 ta dars", lambda: lessons_completed >= 30),
        
        ("xp_500", "🧩", "500 XP", lambda: xp >= 500),
        ("xp_1000", "🧩", "1000 XP", lambda: xp >= 1000),
        ("xp_5000", "🧩", "5000 XP", lambda: xp >= 5000),
    ]

    # Current badges
    current_badges_ids = [b.get("id") for b in g.badges]
    new_badges = []
    
    for b_id, icon, title, check in badges_def:
        if b_id not in current_badges_ids and check():
            new_badge = {
                "id": b_id,
                "icon": icon,
                "title": title,
                "date": timezone.now().isoformat()
            }
            g.badges.append(new_badge)
            new_badges.append(new_badge)
            
    if new_badges:
        g.save(update_fields=["badges", "updated_at"])

def _update_weak_areas(user):
    # Find words with strength < 40
    weak_words = UserWordProgress.objects.filter(user=user, strength__lt=40).select_related("word", "word__category")
    
    # Aggregate by category
    cat_counts = {}
    for wp in weak_words:
        cat_name = wp.word.category.name if wp.word.category else "General"
        cat_counts[cat_name] = cat_counts.get(cat_name, 0) + 1
        
    # Update UserWeakArea
    # Clear old ones? Or update? Let's clear and re-create top 3
    UserWeakArea.objects.filter(user=user).delete()
    
    # Sort by count desc
    sorted_cats = sorted(cat_counts.items(), key=lambda x: x[1], reverse=True)[:3]
    
    for cat, count in sorted_cats:
        # Pct can be just mapped to count for now (e.g. 1 word = 10% urgency, cap at 100%)
        pct = min(100, count * 20) 
        # Ensure key is set
        safe_key = f"cat_{cat.replace(' ', '_').lower()}"[:60]
        UserWeakArea.objects.create(
            user=user,
            key=safe_key,
            title=f"{cat} ({count} words)",
            pct=pct,
            url="/practice/weak/"
        )





# ----------------------------
# TAJWEED HELPERS
# ----------------------------
def _pick_example(level=None, exclude_ids=None):
    qs = TajweedExample.objects.select_related("rule").filter(rule__is_published=True)

    if level:
        qs = qs.filter(rule__level=level)

    if exclude_ids:
        qs = qs.exclude(id__in=exclude_ids)

    return qs.order_by("?").first()


def _build_options(correct_rule, level=None, k=4):
    """
    correct + (k-1) wrong rules
    """
    qs = TajweedRule.objects.filter(is_published=True).exclude(id=correct_rule.id)
    if level:
        qs = qs.filter(level=level)

    wrongs = list(qs.order_by("?")[: max(0, k - 1)])
    options = [correct_rule] + wrongs
    random.shuffle(options)
    return options


# ----------------------------
# TAJWEED LIVE QUIZ (example-based)
# ----------------------------
@login_required
@require_http_methods(["GET", "POST"])
def tajweed_quiz_live(request):
    """
    Live quiz:
      - GET: random example + 4 options
      - POST: check answer + show result
    Query:
      ?level=A0  (optional)
    """
    level = request.GET.get("level")  # A0/A1/A2/B1
    session_key = f"tajweed_quiz_seen_{level or 'all'}"
    seen = request.session.get(session_key, [])
    seen = seen[-50:]  # session kattalashmasin

    if request.method == "GET":
        ex = _pick_example(level=level, exclude_ids=seen) or _pick_example(level=level)
        if not ex:
            return render(request, "tajweed/quiz_empty.html", {"level": level})

        correct_rule = ex.rule
        options = _build_options(correct_rule, level=level, k=4)

        seen.append(ex.id)
        request.session[session_key] = seen
        request.session.modified = True

        marks = ex.marks.select_related("tag", "rule").all()

        return render(
            request,
            "tajweed/quiz_live.html",
            {
                "level": level,
                "example": ex,
                "options": options,
                "marks": marks,
            },
        )

    # POST
    ex_id = request.POST.get("example_id")
    selected_rule_id = request.POST.get("rule_id")

    ex = TajweedExample.objects.select_related("rule").filter(id=ex_id).first()
    if not ex:
        return render(request, "tajweed/quiz_empty.html", {"level": level})

    correct_rule = ex.rule
    selected_rule = TajweedRule.objects.filter(id=selected_rule_id).first() if selected_rule_id else None
    is_correct = bool(selected_rule and selected_rule.id == correct_rule.id)

    TajweedQuizAttempt.objects.create(
        user=request.user,
        example=ex,
        correct_rule=correct_rule,
        selected_rule=selected_rule,
        is_correct=is_correct,
    )

    options = _build_options(correct_rule, level=level, k=4)
    marks = ex.marks.select_related("tag", "rule").all()

    return render(
        request,
        "tajweed/quiz_live_result.html",
        {
            "level": level,
            "example": ex,
            "options": options,
            "selected_rule": selected_rule,
            "correct_rule": correct_rule,
            "is_correct": is_correct,
            "marks": marks,
        },
    )


# ----------------------------
# TAJWEED SIMPLE QUIZ (prompt/options) - NATIJANI SAQLAMAYDI
# (Senda TajweedQuizAttempt modeli quiz/option fieldlarini saqlamaydi.)
# ----------------------------
@login_required
@require_http_methods(["GET", "POST"])
def tajweed_quiz(request):
    """
    GET  -> random TajweedQuiz beradi
    POST -> javobni tekshiradi, natijani ko‘rsatadi
    Eslatma: Hozircha attempt DBga yozilmaydi (model mos emas).
    """
    quiz_id = request.GET.get("id")

    if quiz_id:
        quiz = TajweedQuiz.objects.filter(is_active=True, id=quiz_id).first()
    else:
        quiz = TajweedQuiz.objects.filter(is_active=True).order_by("?").first()

    if not quiz:
        return render(request, "tajweed/quiz_empty.html")

    options = list(quiz.options.all())

    if request.method == "GET":
        return render(request, "tajweed/quiz.html", {"quiz": quiz, "options": options})

    opt_id = request.POST.get("option")
    selected = None
    if opt_id:
        selected = TajweedQuizOption.objects.filter(id=opt_id, quiz=quiz).first()

    is_correct = bool(selected and selected.is_correct)
    correct_opt = quiz.options.filter(is_correct=True).first()

    return render(
        request,
        "tajweed/quiz_result.html",
        {
            "quiz": quiz,
            "options": options,
            "selected": selected,
            "is_correct": is_correct,
            "correct_opt": correct_opt,
        },
    )


def tajweed_index(request):
    q = request.GET.get("q", "").strip()
    level = request.GET.get("level", "").strip()

    rules = TajweedRule.objects.filter(is_published=True)

    if level:
        rules = rules.filter(level=level)

    if q:
        rules = rules.filter(
            Q(title__icontains=q) |
            Q(short_desc__icontains=q) |
            Q(explanation__icontains=q)
        )

    levels = ["A0", "A1", "A2", "B1"]
    
    # Categorize rules for logic-based display
    from collections import defaultdict
    categories = defaultdict(list)
    for rule in rules.order_by("level", "title"):
        categories[rule.get_category_display()].append(rule)

    return render(
        request,
        "tajweed/index.html",
        {
            "categories": dict(categories), 
            "q": q, 
            "level": level, 
            "levels": levels
        },
    )


@login_required
def tajweed_logic_tree(request):
    """
    Interactive 'Rule Finder' logic tree.
    """
    return render(request, "tajweed/logic_tree.html")


@login_required
def tajweed_pro_drill(request):
    """
    Time Attack Version of the Tajweed Quiz.
    """
    level = request.GET.get("level", "A1") # Default to A1 for more content
    # Fetch random examples for the drill
    examples = TajweedExample.objects.filter(rule__level=level).order_by("?")[:15]
    
    if not examples:
        # Fallback to any level if specific level is empty
        examples = TajweedExample.objects.all().order_by("?")[:15]

    if not examples:
        return render(request, "tajweed/quiz_empty.html", {"level": level})

    # Need all rules for the options
    all_rules = TajweedRule.objects.filter(is_published=True).order_by("level", "title")
    
    return render(request, "tajweed/pro_drill.html", {
        "level": level,
        "examples": examples,
        "rules_list": all_rules # Pass simple list instead of complex categories for the quiz script
    })


@login_required
def tajweed_whiteboard(request):
    """
    Whiteboard (Oq doska) for practice.
    """
    letters = Letter.objects.filter(svg_path__isnull=False).exclude(svg_path='').order_by('order')
    return render(request, "tajweed/whiteboard.html", {"letters": letters})


def tajweed_detail(request, slug):
    rule = get_object_or_404(TajweedRule, slug=slug, is_published=True)
    examples = rule.examples.prefetch_related("marks", "marks__tag").all()
    return render(request, "tajweed/detail.html", {"rule": rule, "examples": examples})


# ----------------------------
# PROGRESS HELPERS
# ----------------------------
def _ensure_word_cards(user, lesson, limit=30):
    """
    Lesson ichidagi wordlar uchun review card yaratadi.
    limit: bir marta submitda nechta wordgacha card yaratish.
    """
    words = lesson.words.all().order_by("id")[:limit]
    created = 0

    for w in words:
        if UserCard.objects.filter(user=user, word=w).exists():
            continue
        UserCard.objects.create(
            user=user,
            word=w,
            due_at=timezone.now(),
            repetitions=0,
            interval_days=0,
            ease_factor=2.5,
        )
        created += 1

    return created


def _update_lesson_progress(user, lesson):
    total_ex = lesson.exercises.count()
    if total_ex == 0:
        percent = 0
        completed = False
    else:
        done = (
            UserQuizAttempt.objects
            .filter(user=user, exercise__lesson=lesson)
            .values("exercise_id")
            .distinct()
            .count()
        )
        percent = int((done / total_ex) * 100)
        completed = percent >= 100

    obj, _ = UserLessonProgress.objects.get_or_create(user=user, lesson=lesson)
    obj.percent = max(0, min(100, percent))
    obj.is_completed = completed
    obj.save(update_fields=["percent", "is_completed", "updated_at"])
    return obj


# ----------------------------
# EXERCISES
# ----------------------------
@login_required
def exercise_run(request, pk):
    # Hearts check
    g, _ = UserGamification.objects.get_or_create(user=request.user)
    if g.hearts <= 0:
        return render(request, "pages/no_hearts.html") # We will create this template

    exercise = get_object_or_404(Exercise, pk=pk)
    questions = exercise.questions.prefetch_related("choices").all()
    return render(request, "exercises/run.html", {"exercise": exercise, "questions": questions})


@require_POST
@login_required
@transaction.atomic
def exercise_submit(request, pk):
    exercise = get_object_or_404(Exercise, pk=pk)
    questions = exercise.questions.prefetch_related("choices").all()

    correct = 0
    total = questions.count()
    details = []

    for q in questions:
        picked_raw = request.POST.get(f"q_{q.id}")  # choice_id
        picked_choice = None

        if picked_raw:
            try:
                picked_id = int(picked_raw)
                picked_choice = q.choices.filter(id=picked_id).first()
            except (TypeError, ValueError):
                picked_choice = None

        is_correct = bool(picked_choice and picked_choice.is_correct)
        if is_correct:
            correct += 1
        else:
            # Deduct heart for wrong answer
            g, _ = UserGamification.objects.get_or_create(user=request.user)
            if g.hearts > 0:
                g.hearts -= 1
                g.save()

        correct_choice = q.choices.filter(is_correct=True).first()

        details.append({
            "question": q.text,
            "picked": picked_choice.text if picked_choice else None,
            "correct": correct_choice.text if correct_choice else None,
            "explanation": q.explanation,
            "is_correct": is_correct,
        })

    UserQuizAttempt.objects.create(
        user=request.user,
        exercise=exercise,
        score=correct,
        total=total,
        details={"items": details},
    )

    progress = _update_lesson_progress(request.user, exercise.lesson)
    
    # Update daily stats
    # Update daily stats
    # 5 minutes per exercise approx
    lesson_inc = 1 if progress.is_completed else 0
    stat = _update_daily_stat(request.user, lesson_inc=lesson_inc, minutes_inc=5)
    _check_achievements(request.user, stat=stat)

    created_cards = 0
    if total > 0 and (correct / total) >= 0.6:
        created_cards = _ensure_word_cards(request.user, exercise.lesson, limit=30)

    return render(request, "exercises/result.html", {
        "exercise": exercise,
        "score": correct,
        "total": total,
        "details": details,
        "progress": progress,
        "created_cards": created_cards,
    })


# ----------------------------
# PAGES
# ----------------------------
def home(request):
    total_words = Word.objects.count()
    total_letters = Letter.objects.count()
    active_users = UserGamification.objects.filter(xp_total__gt=0).count() # Real active users
    
    context = {
        "total_words": total_words,
        "total_letters": total_letters,
        "active_users": active_users,
    }
    
    today = timezone.localdate()
    
    if request.user.is_authenticated:
        g, _ = UserGamification.objects.get_or_create(user=request.user)
        context["game"] = g
        context["streak"] = _calc_streak(request.user)
# Add Courses - filter by user's current course level
        user_course = request.user.profile.current_course if hasattr(request.user, 'profile') and request.user.profile.current_course else None
        if user_course:
            # Show only the user's current course level
            context["courses"] = Course.objects.filter(is_published=True, level=user_course.level).order_by("id")
        else:
            # Show all courses if no selection
            context["courses"] = Course.objects.filter(is_published=True).order_by("id")

        return render(request, "dashboard.html", context) # Use new dashboard

    return render(request, "pages/home.html", context)


def roadmap(request):
    levels = ["A0", "A1", "A2", "B1", "Quran"]
    return render(request, "pages/roadmap.html", {"levels": levels})


# ----------------------------
# ALPHABET
# ----------------------------
def alphabet(request):
    letters = Letter.objects.order_by("order")
    return render(request, "alphabet/index.html", {"letters": letters})


def letter_detail(request, pk):
    letter = get_object_or_404(Letter, pk=pk)
    examples = list(letter.examples.all()[:10])

    audio_url = ""
    pr = letter.pronunciations.first()
    if pr and pr.audio:
        audio_url = pr.audio.url

    return render(request, "alphabet/detail.html", {
        "letter": letter,
        "examples": examples,
        "audio_url": audio_url,
    })


@login_required
def letter_practice(request, pk):
    letter = get_object_or_404(Letter, pk=pk)
    
    # 3 ta chalg'ituvchi variant (distractors)
    distractors = list(Letter.objects.exclude(id=letter.id).order_by("?")[:3])
    options = [letter] + distractors
    random.shuffle(options)
    
    # Find next letter logic
    next_letter = Letter.objects.filter(id__gt=letter.id).order_by("id").first()

    return render(request, "alphabet/practice.html", {
        "letter": letter, 
        "options": options,
        "next_letter": next_letter,
    })


@require_POST
@login_required
def api_letter_finish(request, pk):
    """
    Spiral learning tugagach chaqiriladi (Review fazasi).
    SM-2 bo'yicha keyingi qaytarish vaqtini belgilaymiz.
    """
    letter = get_object_or_404(Letter, pk=pk)
    
    # 1. UserCard topish yoki yaratish
    card, created = UserCard.objects.get_or_create(
        user=request.user,
        letter=letter,
        defaults={
            "repetitions": 0,
            "interval_days": 0,
            "ease_factor": 2.5,
            "due_at": timezone.now()
        }
    )
    
    # 2. SM-2 Logic (Simplified)
    # 1-marta o'rgandi -> ertaga qaytaradi
    # Agar review bo'lsa -> interval oshadi
    
    if created or card.repetitions == 0:
        card.interval_days = 1
        card.repetitions = 1
    else:
        # Spiral learningda user "Review" qismi uchun qaytgan bo'lsa:
        # Easy (4) deb hisoblaymiz (chunki bu dars, quiz emas)
        grade = 4 
        card.ease_factor = max(1.3, card.ease_factor + (0.1 - (5 - grade) * (0.08 + (5 - grade) * 0.02)))
        
        if card.repetitions == 1:
            card.interval_days = 6
        else:
            card.interval_days = int(card.interval_days * card.ease_factor)
            
        card.repetitions += 1

    card.due_at = timezone.now() + timedelta(days=card.interval_days)
    card.save()

    # 3. XP berish (Optional)
    g, _ = UserGamification.objects.get_or_create(user=request.user)
    g.xp_total += 10
    g.save()

    return JsonResponse({
        "status": "ok", 
        "next_review": card.due_at.strftime("%Y-%m-%d"),
        "xp_added": 10
    })


# ----------------------------
# COURSES
# ----------------------------
def course_list(request):
    courses = Course.objects.filter(is_published=True).order_by("level", "id")
    return render(request, "courses/list.html", {"courses": courses})


@login_required
def course_detail(request, pk):
    course = get_object_or_404(Course, pk=pk)
    units = course.units.prefetch_related("lessons", "lessons__videos").all()
    
    # Fetch progress for all lessons in this course
    progress_map = {}
    if request.user.is_authenticated:
        from .models import UserLessonProgress
        lessons_ids = []
        for u in units:
            lessons_ids.extend([l.id for l in u.lessons.all()])
        
        progs = UserLessonProgress.objects.filter(user=request.user, lesson_id__in=lessons_ids)
        progress_map = {p.lesson_id: p for p in progs}

    # Attach progress to lesson objects
    for u in units:
        for l in u.lessons.all():
            l.user_prog = progress_map.get(l.id)

    return render(request, "courses/detail.html", {
        "course": course,
        "units": units
    })

@login_required
def api_user_stats(request):
    """
    Real-time XP updates via polling.
    """
    g, _ = UserGamification.objects.get_or_create(user=request.user)
    streak = _calc_streak(request.user)
    return JsonResponse({
        "xp": g.xp_total,
        "level": g.level,
        "hearts": g.hearts,
        "streak": streak["current_streak"]
    })


@login_required
def lesson_detail(request, pk):
    lesson = get_object_or_404(Lesson, pk=pk)

    # Locking logic (Prev lesson completion)
    prev = Lesson.objects.filter(unit=lesson.unit, order__lt=lesson.order).order_by("-order").first()
    if prev:
        if not UserLessonProgress.objects.filter(user=request.user, lesson=prev, is_completed=True).exists():
             return render(request, "pages/locked.html")

    # If the lesson has blocks, we might want to redirect to the first block/exercise
    if lesson.blocks:
        # For now, let's just render the detail which will have a "Start" button
        pass

    return render(request, "lessons/detail.html", {"lesson": lesson})

# ----------------------------
# COURSE SELECTION
# ----------------------------
@login_required
def course_selection(request):
    # Ensure profile exists safely
    profile, created = Profile.objects.get_or_create(user=request.user)
    
    if request.method == "POST":
        course_id = request.POST.get("course_id")
        if not course_id:
            messages.error(request, "Iltimos, avval kursni tanlang!")
            return redirect("arab:course_selection")

        course = get_object_or_404(Course, id=course_id)
        
        profile.current_course = course
        profile.save()
        
        messages.success(request, f"{course.title} kursi tanlandi!")
        return redirect("arab:home")
        
    courses = Course.objects.filter(is_published=True).order_by("id")
    current_course = profile.current_course
    
    return render(request, "courses/selection.html", {
        "courses": courses,
        "current_course": current_course
    })


@login_required
def video_detail(request, pk):
    video = get_object_or_404(LessonVideo, pk=pk)
    
    # Progress check
    prog, _ = UserVideoProgress.objects.get_or_create(user=request.user, video=video)
    
    # Prev/Next logic
    next_video = LessonVideo.objects.filter(lesson=video.lesson, order__gt=video.order).order_by("order").first()
    prev_video = LessonVideo.objects.filter(lesson=video.lesson, order__lt=video.order).order_by("-order").first()
    
    # Related (Same unit)
    related_videos = LessonVideo.objects.filter(lesson__unit=video.lesson.unit).exclude(id=video.id).order_by("?")[:4]

    return render(request, "lessons/video.html", {
        "video": video, 
        "progress": prog,
        "next_video": next_video,
        "prev_video": prev_video,
        "related_videos": related_videos
    })


@require_POST
@login_required
def video_progress(request, pk):
    """
    AJAX: Update video progress
    payload: {seconds: 120}
    """
    video = get_object_or_404(LessonVideo, pk=pk)
    seconds = int(request.POST.get("seconds", 0))
    
    prog, _ = UserVideoProgress.objects.get_or_create(user=request.user, video=video)
    prog.progress_seconds = seconds
    
    # 80% rule
    if not prog.is_watched and video.duration > 0:
        if seconds >= (video.duration * 0.8):
            prog.is_watched = True
            
            # Award XP (once)
            g, _ = UserGamification.objects.get_or_create(user=request.user)
            g.xp_total += 20
            g.save()
            
            # Update daily stat
            _update_daily_stat(request.user, minutes_inc=1) # Minimal inc
            
    prog.save()
    
    return JsonResponse({"status": "ok", "watched": prog.is_watched})


@login_required
def video_library(request):
    """
    Barcha video darslarni ko'rsatish
    """
    videos = LessonVideo.objects.select_related("lesson", "lesson__unit", "lesson__unit__course").order_by("-created_at")
    
    # Filter by q
    q = request.GET.get("q", "")
    if q:
        videos = videos.filter(title__icontains=q)
    
    # Filter by level
    level = request.GET.get("level", "")
    if level:
        videos = videos.filter(lesson__unit__course__level=level)
        
    levels = [l[0] for l in Course.LEVEL_CHOICES]
    
    return render(request, "lessons/library.html", {
        "videos": videos, 
        "q": q, 
        "level": level,
        "levels": levels
    })


# ----------------------------
# PRACTICE
# ----------------------------
@login_required
def practice_hub(request):
    user = request.user
    game = UserGamification.objects.filter(user=user).first()
    streak_data = _calc_streak(user)
    
    # Weekly Activity (Last 7 days)
    today = timezone.localdate()
    week_stats = []
    for i in range(6, -1, -1):
        day = today - timedelta(days=i)
        stat = UserDailyStat.objects.filter(user=user, day=day).first()
        
        # Determine if goal met (Simplified goal: 10xp or 5min or 1 lesson)
        goal_met = False
        if stat:
            goal_met = (stat.xp_earned >= 10) or (stat.study_minutes >= 5) or (stat.lessons_done >= 1)
            
        week_stats.append({
            "day_name": day.strftime("%a"),
            "is_today": day == today,
            "goal_met": goal_met,
            "has_data": stat is not None
        })
    
    return render(request, "practice/index.html", {
        "game": game,
        "streak_data": streak_data,
        "current_streak": streak_data.get("current_streak", 0),
        "week_stats": week_stats,
        "total_words": Word.objects.count(),
        "total_letters": Letter.objects.count(),
    })

@require_POST
@login_required
def update_study_time(request):
    """
    AJAX: Increment study minutes
    """
    _update_daily_stat(request.user, minutes_inc=1)
    return JsonResponse({"status": "ok"})

@login_required
def get_live_stats(request):
    """
    AJAX: Get latest XP and Level
    """
    g, _ = UserGamification.objects.get_or_create(user=request.user)
    
    current_level = g.level
    xp_total = g.xp_total

    # Calculate thresholds
    # Previous level max XP (start of current level)
    prev_threshold = xp_for_next_level(current_level - 1) if current_level > 1 else 0
    # Next level max XP (end of current level)
    next_threshold = xp_for_next_level(current_level)

    # Progress with in level
    level_xp_gained = max(0, xp_total - prev_threshold)
    level_width = max(1, next_threshold - prev_threshold) # Prevent div by zero
    
    xp_pct = min(100, int((level_xp_gained / level_width) * 100))

    return JsonResponse({
        "xp": xp_total,
        "level": current_level,
        "next_level_xp": next_threshold,
        "xp_pct": xp_pct,
        "level_xp_current": level_xp_gained, # Optional: display 500/1000
        "level_xp_max": level_width
    })


# ----------------------------
# REVIEW
# ----------------------------



@login_required
def review(request):
    now = timezone.now()
    cards = (
        UserCard.objects
        .filter(user=request.user, due_at__lte=now)
        .select_related("word", "letter")
        .order_by("due_at")[:20]
    )
    return render(request, "review/index.html", {"cards": cards})


@login_required
def review_grade(request, card_id, grade):
    """
    grade: 0..5 (SM-2)
    """
    card = get_object_or_404(UserCard, id=card_id, user=request.user)
    grade = max(0, min(5, int(grade)))

    ef = card.ease_factor
    rep = card.repetitions
    interval = card.interval_days

    if grade < 3:
        rep = 0
        interval = 1
    else:
        if rep == 0:
            interval = 1
        elif rep == 1:
            interval = 6
        else:
            interval = int(round(interval * ef))
        rep += 1

    ef = ef + (0.1 - (5 - grade) * (0.08 + (5 - grade) * 0.02))
    if ef < 1.3:
        ef = 1.3

    card.ease_factor = ef
    card.repetitions = rep
    card.interval_days = max(1, interval)
    card.due_at = timezone.now() + timedelta(days=card.interval_days)
    card.save(update_fields=["ease_factor", "repetitions", "interval_days", "due_at", "updated_at"])

    if card.word_id:
        obj, _ = UserWordProgress.objects.get_or_create(user=request.user, word=card.word)
        if grade >= 4:
            obj.strength = min(100, obj.strength + 10)
        elif grade == 3:
            obj.strength = min(100, obj.strength + 5)
        else:
            obj.strength = max(0, obj.strength - 5)
        obj.last_seen = timezone.now()
        obj.save(update_fields=["strength", "last_seen", "updated_at"])
        
        # Check weak areas if strength dropped
        if obj.strength < 40:
             _update_weak_areas(request.user)

    # Update daily stats
    stat = _update_daily_stat(request.user, review_inc=1, minutes_inc=1)
    
    # Restore heart if good grade
    if grade >= 3:
        g, _ = UserGamification.objects.get_or_create(user=request.user)
        if g.hearts < 5:
            g.hearts += 1
        
        # XP for good review
        g.xp_total += 5
        g.save()
        _check_achievements(request.user, stat=stat)

    return redirect("arab:review")


# (Legacy placement_test removed to avoid conflict)
def legacy_placement_test_cleanup():
    pass
# (Cleanup complete)


# ----------------------------
# DICTIONARY
# ----------------------------
@login_required
def dictionary(request):
    q = request.GET.get("q", "").strip()
    cat = request.GET.get("cat", "").strip()
    alpha = request.GET.get("alpha", "").strip()
    page_number = request.GET.get("page", 1)

    words = Word.objects.select_related("category").all()

    if q:
        words = words.filter(
            Q(arabic__icontains=q) |
            Q(transliteration__icontains=q) |
            Q(pronunciation__icontains=q) |
            Q(translation_uz__icontains=q) |
            Q(translation_ru__icontains=q)
        )

    if cat:
        words = words.filter(category__name__iexact=cat)
        
    if alpha:
        # Detect if it's an Arabic character (roughly 0x0600 to 0x06FF range)
        if any('\u0600' <= char <= '\u06FF' for char in alpha):
            words = words.filter(arabic__startswith=alpha)
        else:
            words = words.filter(transliteration__istartswith=alpha)

    # Order by arabic by default, or translit if requested
    words = words.order_by("arabic")

    paginator = Paginator(words, 20) # 20 ta so'z bir sahifada
    page_obj = paginator.get_page(page_number)

    return render(
        request, 
        "dictionary/index.html", 
        {
            "page_obj": page_obj,
            "q": q, 
            "cat": cat,
            "alpha": alpha
        }
    )

@login_required
def dictionary_add_card(request, word_id):
    if request.method == "POST":
        word = get_object_or_404(Word, id=word_id)
        # Create a card if it doesn't exist
        # NOTE: UserWordProgress fields are 'strength', 'last_seen'. 
        # But 'dictionary_add_card' likely implies adding to 'UserCard' (Review list) as well?
        # If we want to add to REVIEW list, we should create a UserCard.
        # But the existing code was creating UserWordProgress. 
        # Let's create UserWordProgress with valid defaults.
        # AND also create UserCard if needed?
        # Based on naming 'add_card', it implies UserCard.
        # Check models: UserCard links to Word.
        
        # 1. Ensure UserWordProgress exists (for stats)
        prog, _ = UserWordProgress.objects.get_or_create(
            user=request.user,
            word=word,
            defaults={'strength': 0, 'last_seen': timezone.now()}
        )
        
        # 2. Ensure UserCard exists (for review)
        card, created = UserCard.objects.get_or_create(
            user=request.user,
            word=word,
            defaults={
                'repetitions': 0, 
                'interval_days': 1, 
                'ease_factor': 2.5,
                'due_at': timezone.now()
            }
        )
        if created:
            # Award some XP for saving a word
            g, _ = UserGamification.objects.get_or_create(user=request.user)
            g.xp_total += 2
            g.save()
            _update_daily_stat(request.user, new_word_inc=1)
            _check_achievements(request.user)
            return JsonResponse({"status": "created", "msg": "So'z takrorlash ro'yxatiga qo'shildi! +2 XP"})
        return JsonResponse({"status": "exists", "msg": "Bu so'z allaqachon ro'yxatingizda bor."})
    return JsonResponse({"status": "error"}, status=400)


# ----------------------------
# PROGRESS
# ----------------------------



# ----------------------------
# AUTH
# ----------------------------
def register(request):
    if request.user.is_authenticated:
        return redirect("arab:progress")

    if request.method == "POST":
        form = RegisterForm(request.POST)
        if form.is_valid():
            try:
                user = form.save()
                login(request, user, backend='django.contrib.auth.backends.ModelBackend')
                # Set a flag to show a welcome quiz/message
                request.session['show_welcome_quiz'] = True
                return redirect("arab:progress")
            except Exception as e:
                form.add_error(None, f"Xatolik yuz berdi: {e}")
    else:
        form = RegisterForm()

    return render(request, "auth/register.html", {"form": form})


def login_view(request):
    if request.user.is_authenticated:
        return redirect("arab:progress")

    error = ""
    form = LoginForm()
    
    if request.method == "POST":
        form = LoginForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data.get("username")
            password = form.cleaned_data.get("password")
            
            try:
                user = authenticate(request, username=username, password=password)
                if user is not None:
                    login(request, user)
                    # Trigger quiz on next redirect
                    request.session['just_logged_in'] = True
                    return redirect("arab:progress")
                else:
                    error = "Login yoki parol noto'g'ri."
            except Exception as e:
                import logging
                logging.error(f"Login error: {e}")
                error = "Tizim xatoligi yuz berdi. Iltimos qayta urinib ko'ring."
        else:
            error = "Ma'lumotlarni to'liq kiriting."

    return render(request, "auth/login.html", {"form": form, "error": error})


@login_required
def progress(request):
    user = request.user
    today = timezone.localdate()

    # Daily targets (xohlasangiz UserSettings qilib DBdan ham qilsangiz bo'ladi)
    daily_review_target = 10
    daily_new_words_target = 5
    daily_lessons_target = 1

    # Today stat
    today_stat, _ = UserDailyStat.objects.get_or_create(user=user, day=today)

    # Streak
    streak = _calc_streak(user)

    # Due count (Actual data from SM-2 cards)
    due_count = UserCard.objects.filter(user=user, due_at__lte=timezone.now()).count()

    # Words
    learned_words = UserDailyStat.objects.filter(user=user).aggregate(s=Sum("new_words"))["s"] or 0
    total_words = Word.objects.count()
    words_pct = int((learned_words / max(1, total_words)) * 100)

    # Lessons (Real Data)
    lessons_completed = UserLessonProgress.objects.filter(user=user, is_completed=True).count()
    lessons_total = Lesson.objects.count()
    lessons_pct = int((lessons_completed / max(1, lessons_total)) * 100)

    # Quiz Accuracy
    attempts = UserQuizAttempt.objects.filter(user=user)
    q_score = attempts.aggregate(s=Sum('score'))['s'] or 0
    q_total = attempts.aggregate(s=Sum('total'))['s'] or 0
    quiz_accuracy = int((q_score / q_total) * 100) if q_total > 0 else 0

    # Gamification
    g, _ = UserGamification.objects.get_or_create(user=user)
    level = g.level or 1
    xp = g.xp_total or 0
    xp_next = max(100, xp_for_next_level(level))
    xp_in_level = xp % xp_next
    xp_pct = int((xp_in_level / max(1, xp_next)) * 100)
    xp_remaining = max(0, xp_next - xp_in_level)

    # Study time
    week_start = today - timedelta(days=6)
    last7 = list(UserDailyStat.objects.filter(user=user, day__gte=week_start, day__lte=today).order_by("day"))
    study_today_min = today_stat.study_minutes
    study_week_min = sum(x.study_minutes for x in last7)
    study_avg_min = int(study_week_min / 7)

    # Weekly bars
    week_total_actions = 0
    week_bars = []
    for s in last7:
        actions = (s.reviews_done or 0) + (s.new_words or 0) + (s.lessons_done or 0)
        week_total_actions += actions
        week_bars.append({"label": s.day.strftime("%a"), "raw": actions})

    max_actions = max([b["raw"] for b in week_bars], default=0)
    for b in week_bars:
        b["pct"] = int((b["raw"] / max(1, max_actions)) * 100) if max_actions else 0

    # Recommendations
    recommendations = []
    if due_count > 0:
        recommendations.append({"title": "Review qil", "desc": f"{due_count} ta card kutyapti", "url": "/review/"})
    if lessons_completed < lessons_total:
        recommendations.append({"title": "Kurs davom et", "desc": "1 ta dars tugat", "url": "/courses/"})
    if learned_words < total_words:
        recommendations.append({"title": "5 ta yangi so‘z", "desc": "Lug‘atdan o‘rgan", "url": "/dictionary/"})
    if not recommendations:
        recommendations.append({"title": "Practice", "desc": "10 daqiqa mashq qil", "url": "/practice/"})

    # Achievements
    achievements = g.badges
    # If empty, maybe show placeholders or just empty list
    if not achievements:
        achievements = []

    # Weak areas
    weak_areas_qs = UserWeakArea.objects.filter(user=user).order_by("pct")[:3]
    weak_areas = [{"title": w.title, "pct": w.pct, "url": w.url} for w in weak_areas_qs]

    # Heatmap
    days_back = 70
    start_day = today - timedelta(days=days_back - 1)

    stats_map = {
        s.day: s for s in UserDailyStat.objects.filter(user=user, day__gte=start_day, day__lte=today)
    }

    def intensity(s: UserDailyStat | None) -> float:
        if not s: return 0.05
        score = (s.reviews_done or 0) + (s.new_words or 0) * 2 + (s.lessons_done or 0) * 5 + (s.study_minutes or 0) * 0.1
        if score <= 0: return 0.05
        if score < 5: return 0.18
        if score < 15: return 0.35
        if score < 30: return 0.55
        return 0.85

    heatmap = []
    cur = start_day
    for _w in range(10):  # 10 haftalik ko'rinish
        row = []
        for _d in range(7):
            st = stats_map.get(cur)
            row.append(intensity(st))
            cur += timedelta(days=1)
        heatmap.append(row)

    # Missions
    missions = _get_daily_missions(user)

    # Check for post-login actions
    # Quiz trigger logic
    show_welcome_quiz = False
    show_daily_quiz = False

    if request.session.pop('just_logged_in', False):
        # Agar hali placement test topshirmagan bo'lsa - Welcome Quiz
        if not hasattr(user, 'profile') or not user.profile.has_taken_placement_test:
            show_welcome_quiz = True
        else:
            # Agar bugun hali review yoki lesson qilinmagan bo'lsa - Daily Quiz
            daily_goal_met = ((today_stat.reviews_done or 0) >= daily_review_target or 
                             (today_stat.lessons_done or 0) >= daily_lessons_target)
            if not daily_goal_met:
                show_daily_quiz = True

    context = {
        "show_welcome_quiz": show_welcome_quiz,
        "show_daily_quiz": show_daily_quiz,
        "streak": streak,
        "due_count": due_count,
        "learned_words": learned_words,
        "total_words": total_words,
        "words_pct": words_pct,
        "lessons_completed": lessons_completed,
        "lessons_total": lessons_total,
        "lessons_pct": lessons_pct,
        "quiz_accuracy": quiz_accuracy,
        "daily_review_target": daily_review_target,
        "daily_new_words_target": daily_new_words_target,
        "daily_lessons_target": daily_lessons_target,
        "today_review_done": today_stat.reviews_done,
        "today_new_words": today_stat.new_words,
        "today_lessons_done": today_stat.lessons_done,
        "level": level,
        "xp": xp,
        "xp_next": xp_next,
        "xp_pct": xp_pct,
        "xp_remaining": xp_remaining,
        "study_today_min": study_today_min,
        "study_week_min": study_week_min,
        "study_avg_min": study_avg_min,
        "week_bars": week_bars,
        "week_total_actions": week_total_actions,
        "rank_name": "Bronze" if (xp or 0) < 500 else "Silver" if (xp or 0) < 1000 else "Gold",
        "recommendations": recommendations,
        "achievements": achievements,
        "weak_areas": weak_areas,
        "heatmap": heatmap,
        "missions": missions,
    }
    return render(request, "progress/index.html", context)


@login_required
def logout_view(request):
    logout(request)
    return redirect("arab:home")


# ----------------------------
# WEAK WORDS
# ----------------------------
@login_required
def practice_weak_words(request):
    if request.method == "POST":
        # Simple processing
        return redirect("arab:progress")

    weak_qs = UserWordProgress.objects.filter(user=request.user, strength__lt=40).select_related("word")[:10]
    if not weak_qs.exists():
        return render(request, "practice/weak_empty.html")

    quiz_items = []
    all_translations = list(Word.objects.exclude(translation_uz="").values_list("translation_uz", flat=True))

    for p in weak_qs:
        correct = p.word.translation_uz
        # pick 3 wrong
        others = [x for x in all_translations if x != correct]
        if len(others) < 3:
            distractors = others
        else:
            distractors = random.sample(others, 3)
        
        options = distractors + [correct]
        random.shuffle(options)
        
        quiz_items.append({
            "word": p.word,
            "options": options
        })

    return render(request, "practice/weak_words.html", {"items": quiz_items})
@login_required
def settings_profile(request):
    profile, created = Profile.objects.get_or_create(user=request.user)
    reminder, _ = UserReminder.objects.get_or_create(user=request.user)
    
    if request.method == 'POST':
        u_form = UserUpdateForm(request.POST, instance=request.user)
        p_form = ProfileUpdateForm(request.POST, request.FILES, instance=profile)
        r_form = ReminderUpdateForm(request.POST, instance=reminder)
        
        if u_form.is_valid() and p_form.is_valid() and r_form.is_valid():
            u_form.save()
            p_form.save()
            r_form.save()
            messages.success(request, f'Profilingiz muvaffaqiyatli yangilandi!')
            return redirect('arab:settings_profile')
    else:
        u_form = UserUpdateForm(instance=request.user)
        p_form = ProfileUpdateForm(instance=profile)
        r_form = ReminderUpdateForm(instance=reminder)

    context = {
        'u_form': u_form,
        'p_form': p_form,
        'r_form': r_form
    }
    return render(request, 'auth/profile_settings.html', context)

@login_required
def settings_password(request):
    if request.method == 'POST':
        form = PasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)  # Important!
            messages.success(request, 'Parolingiz muvaffaqiyatli yangilandi!')
            return redirect('arab:settings_password')
        else:
            messages.error(request, 'Iltimos xatolarni tuzating.')
    else:
        form = PasswordChangeForm(request.user)
    return render(request, 'auth/password_settings.html', {'form': form})


# ----------------------------
# QURAN
# ----------------------------
@login_required
def quran_index(request):
    surahs = QuranSurah.objects.all()
    
    # Check if Fatiha exists and needs coloring update (Fix/Upgrade)
    # We check if the first ayah contains HTML. If not, we force re-create/update.
    fatiha = QuranSurah.objects.filter(number=1).first()
    if fatiha:
        first_ayah = fatiha.ayahs.filter(number_in_surah=1).first()
        if first_ayah and "<span" not in first_ayah.text:
            # Re-apply coloring logic
            fatiha.ayahs.all().delete()
            # 1. Bismillah: Ar-Rahm[aa]n (Madd), Ar-Rah[ee]m (Madd)
            QuranAyah.objects.create(surah=fatiha, number_in_surah=1, text='بِسْمِ ٱللَّهِ ٱلرَّحْمَ<span class="text-rose-300 bg-rose-500/10 rounded px-1">ـٰ</span>نِ ٱلرَّحِ<span class="text-rose-300 bg-rose-500/10 rounded px-1">ي</span>مِ')
            # 2. Alon
            QuranAyah.objects.create(surah=fatiha, number_in_surah=2, text='ٱلْحَمْدُ لِلَّهِ رَبِّ ٱلْعَ<span class="text-rose-300 bg-rose-500/10 rounded px-1">ـٰ</span>لَمِ<span class="text-rose-300 bg-rose-500/10 rounded px-1">ي</span>نَ')
            # 3. Ar-Rahman
            QuranAyah.objects.create(surah=fatiha, number_in_surah=3, text='ٱلرَّحْمَ<span class="text-rose-300 bg-rose-500/10 rounded px-1">ـٰ</span>نِ ٱلرَّحِ<span class="text-rose-300 bg-rose-500/10 rounded px-1">ي</span>مِ')
            # 4. Maliki (Maa - Rose)
            QuranAyah.objects.create(surah=fatiha, number_in_surah=4, text='مَ<span class="text-rose-300 bg-rose-500/10 rounded px-1">ـٰ</span>لِكِ يَوْمِ ٱلدِّي<span class="text-rose-300 bg-rose-500/10 rounded px-1">نِ</span>')
            # 5. Iyyaka (Shadda - Emerald?), Nasta'een (Madd - Rose)
            QuranAyah.objects.create(surah=fatiha, number_in_surah=5, text='إِيَّاكَ نَعْبُدُ وَإِيَّاكَ نَسْتَعِ<span class="text-rose-300 bg-rose-500/10 rounded px-1">ي</span>نُ')
            # 6. Ihdina (Qalqala? No). Sirat (Saad - Heavy? Violet). Mustaqeem (Qalqala qaf? No).
            QuranAyah.objects.create(surah=fatiha, number_in_surah=6, text='ٱهْدِنَا ٱلصِّرَ<span class="text-rose-300 bg-rose-500/10 rounded px-1">ٰ</span>طَ ٱلْمُسْتَقِ<span class="text-rose-300 bg-rose-500/10 rounded px-1">ي</span>مَ')
            # 7. Sirat...
            QuranAyah.objects.create(surah=fatiha, number_in_surah=7, text='صِرَ<span class="text-rose-300 bg-rose-500/10 rounded px-1">ٰ</span>طَ ٱلَّذِينَ أَنْعَمْتَ عَلَيْهِمْ غَيْرِ ٱلْمَغْضُوبِ عَلَيْهِمْ وَلَا ٱلضَّ<span class="text-rose-300 bg-rose-500/10 rounded px-1">آ</span>لِّ<span class="text-rose-300 bg-rose-500/10 rounded px-1">ي</span>نَ')

    if not surahs.exists():
        # Auto-create Fatiha for demo if empty
        if not QuranSurah.objects.exists():
            s = QuranSurah.objects.create(
                number=1, name="Al-Fatiha", english_name="The Opening", ayah_count=7, place="Mecca"
            )
            # Add Basmala + some ayahs with manual coloring (Demo)
            # 1. Bismillah: Ar-Rahm[aa]n (Madd), Ar-Rah[ee]m (Madd)
            QuranAyah.objects.create(surah=s, number_in_surah=1, text='بِسْمِ ٱللَّهِ ٱلرَّحْمَ<span class="text-rose-300 bg-rose-500/10 rounded px-1">ـٰ</span>نِ ٱلرَّحِ<span class="text-rose-300 bg-rose-500/10 rounded px-1">ي</span>مِ')
            
            # 2. Alon
            QuranAyah.objects.create(surah=s, number_in_surah=2, text='ٱلْحَمْدُ لِلَّهِ رَبِّ ٱلْعَ<span class="text-rose-300 bg-rose-500/10 rounded px-1">ـٰ</span>لَمِ<span class="text-rose-300 bg-rose-500/10 rounded px-1">ي</span>نَ')
            
            # 3. Ar-Rahman
            QuranAyah.objects.create(surah=s, number_in_surah=3, text='ٱلرَّحْمَ<span class="text-rose-300 bg-rose-500/10 rounded px-1">ـٰ</span>نِ ٱلرَّحِ<span class="text-rose-300 bg-rose-500/10 rounded px-1">ي</span>مِ')
            
            # 4. Maliki (Maa - Rose)
            QuranAyah.objects.create(surah=s, number_in_surah=4, text='مَ<span class="text-rose-300 bg-rose-500/10 rounded px-1">ـٰ</span>لِكِ يَوْمِ ٱلدِّي<span class="text-rose-300 bg-rose-500/10 rounded px-1">نِ</span>')
            
            # 5. Iyyaka (Shadda - Emerald?), Nasta'een (Madd - Rose)
            QuranAyah.objects.create(surah=s, number_in_surah=5, text='إِيَّاكَ نَعْبُدُ وَإِيَّاكَ نَسْتَعِ<span class="text-rose-300 bg-rose-500/10 rounded px-1">ي</span>نُ')
            
            # 6. Ihdina (Qalqala? No). Sirat (Saad - Heavy? Violet). Mustaqeem (Qalqala qaf? No).
            QuranAyah.objects.create(surah=s, number_in_surah=6, text='ٱهْدِنَا ٱلصِّرَ<span class="text-rose-300 bg-rose-500/10 rounded px-1">ٰ</span>طَ ٱلْمُسْتَقِ<span class="text-rose-300 bg-rose-500/10 rounded px-1">ي</span>مَ')
            
            # 7. Sirat... Ghayri (Ghayn - heavy). Maghdoobi (Madd). Walad-daalleen (Madd Lazim - 6 harakat - BIG Rose/Red + Shadda)
            # Daalleen: Madd (Rose) + Shadda (Amber?)
            QuranAyah.objects.create(surah=s, number_in_surah=7, text='صِرَ<span class="text-rose-300 bg-rose-500/10 rounded px-1">ٰ</span>طَ ٱلَّذِينَ أَنْعَمْتَ عَلَيْهِمْ غَيْرِ ٱلْمَغْضُوبِ عَلَيْهِمْ وَلَا ٱلضَّ<span class="text-rose-300 bg-rose-500/10 rounded px-1">آ</span>لِّ<span class="text-rose-300 bg-rose-500/10 rounded px-1">ي</span>نَ')
        surahs = QuranSurah.objects.all()

    return render(request, "quran/index.html", {"surahs": surahs})


@login_required
def quran_detail(request, surah_number):
    surah = get_object_or_404(QuranSurah, number=surah_number)
    ayahs = surah.ayahs.all()
    
    # Simple navigation
    prev_surah = QuranSurah.objects.filter(number__lt=surah.number).last()
    next_surah = QuranSurah.objects.filter(number__gt=surah.number).first()
    
    return render(request, "quran/detail.html", {
        "surah": surah, 
        "ayahs": ayahs,
        "prev_surah": prev_surah,
        "next_surah": next_surah
    })





# ----------------------------
# ERROR HANDLERS
# ----------------------------
def custom_404(request, exception):
    return render(request, "404.html", status=404)

def custom_500(request):
    return render(request, "500.html", status=500)

# ----------------------------
# MATCH GAME
# ----------------------------
@login_required
def practice_match_game(request):
    # Fetch random 6 words that have translations AND are not marked [EN]
    words = list(Word.objects.filter(translation_uz__isnull=False).exclude(translation_uz="").exclude(translation_uz__startswith="[EN]").order_by("?")[:6])
    
    # Fallback if not enough translated words
    if len(words) < 6:
        defaults = list(Word.objects.filter(translation_uz__isnull=False).exclude(translation_uz="").order_by("?")[:(6 - len(words))])
        words.extend(defaults)

    # Prepare data for frontend
    game_data = []
    for w in words:
        # Strip [EN] just in case we used fallback
        clean_gloss = w.translation_uz.replace("[EN]", "").strip()
        game_data.append({
            "id": w.id,
            "arabic": w.arabic,
            "translation": clean_gloss
        })
    
    return render(request, "practice/match_game.html", {"game_data": json.dumps(game_data)})

@login_required
@require_POST
def api_match_reward(request):
    try:
        data = json.loads(request.body)
        matches_count = data.get("matches", 0)
        
        if matches_count > 0:
            # +10 XP per match
            xp = matches_count * 10
            
            # Update stats
            today = timezone.localdate()
            s, _ = UserDailyStat.objects.get_or_create(user=request.user, day=today)
            s.xp_earned += xp
            s.save()
            
            # Update gamification profile
            g, _ = UserGamification.objects.get_or_create(user=request.user)
            g.xp_total += xp
            current_xp = g.xp_total
            g.save()
            
            # Check level up
            if current_xp >= xp_for_next_level(g.level):
                 g.level += 1
                 g.save()
                 
            return JsonResponse({"status": "ok", "xp_gained": xp, "new_total": current_xp})
            
        return JsonResponse({"status": "ok", "xp_gained": 0})
    except Exception as e:
        return JsonResponse({"status": "error", "message": str(e)}, status=400)


@login_required
def placement_test(request):
    if request.method == "POST":
        correct_count = 0
        total_questions = PlacementQuestion.objects.count()
        for key, value in request.POST.items():
            if key.startswith("q_"):
                q_id = key.split("_")[1]
                if PlacementOption.objects.filter(id=value, question_id=q_id, is_correct=True).exists():
                    correct_count += 1
        if total_questions > 0:
            percentage = (correct_count / total_questions) * 100
            if percentage < 30: level = "A0"
            elif percentage < 60: level = "A1"
            elif percentage < 85: level = "A2"
            else: level = "B1"
        else:
            level = "A0"
        profile, _ = Profile.objects.get_or_create(user=request.user)
        suggested_course = Course.objects.filter(level=level).first()
        if suggested_course:
            profile.current_course = suggested_course
        profile.has_taken_placement_test = True
        profile.save()
        messages.success(request, f"Sizning darajangiz: {level}. {suggested_course.title if suggested_course else 'Kurs tanlang'}!")
        return redirect("arab:progress")
    questions = PlacementQuestion.objects.prefetch_related("options").all()
    if not questions.exists():
        messages.info(request, "Hozircha placement test savollari yo'q. A0 darajadan boshlang.")
        return redirect("arab:home")
    return render(request, "pages/placement.html", {"questions": questions})


@login_required
def lesson_run(request, pk):
    lesson = get_object_or_404(Lesson, pk=pk)
    block_index = int(request.GET.get("block", 0))
    if not lesson.blocks or block_index >= len(lesson.blocks):
        _update_lesson_progress(request.user, lesson)
        g, _ = UserGamification.objects.get_or_create(user=request.user)
        g.xp_total += 50
        g.save()
        messages.success(request, f"{lesson.title} muvaffaqiyatli tugatildi! +50 XP")
        return redirect("arab:home")
    current_block = lesson.blocks[block_index]
    total_blocks = len(lesson.blocks)
    progress_pct = int(((block_index) / total_blocks) * 100)
    context = {
        "lesson": lesson,
        "block": current_block,
        "block_index": block_index,
        "next_block_index": block_index + 1,
        "total_blocks": total_blocks,
        "progress_pct": progress_pct,
    }
    if current_block["type"] == "vocabulary":
        word_ids = current_block.get("word_ids", [])
        context["words"] = Word.objects.filter(id__in=word_ids)
    return render(request, "lessons/run.html", context)


@login_required
@require_POST
def api_lesson_submit(request, pk):
    return JsonResponse({"status": "ok", "xp_gained": 10})

# ----------------------------
# SCENARIOS / CONVERSATIONAL
# ----------------------------

@login_required
def scenario_list(request):
    categories = ScenarioCategory.objects.prefetch_related("scenarios").all()
    recent_scenarios = Scenario.objects.filter(is_published=True).order_by("-created_at")[:5]
    return render(request, "scenarios/list.html", {
        "categories": categories,
        "recent_scenarios": recent_scenarios
    })


@login_required
def scenario_detail(request, pk):
    scenario = get_object_or_404(Scenario.objects.prefetch_related("dialog_lines"), pk=pk)
    return render(request, "scenarios/detail.html", {
        "scenario": scenario,
        "dialog_lines": scenario.dialog_lines.all()
    })


@login_required
def phrasebook(request):
    category_id = request.GET.get("category")
    scenario_id = request.GET.get("scenario")
    
    phrases = PhrasebookEntry.objects.all()
    
    if category_id:
        phrases = phrases.filter(category_id=category_id)
    if scenario_id:
        phrases = phrases.filter(scenario_id=scenario_id)
        
    categories = ScenarioCategory.objects.all()
    
    return render(request, "scenarios/phrasebook.html", {
        "phrases": phrases,
        "categories": categories,
        "current_category": category_id,
        "current_scenario": scenario_id
    })


@login_required
def leagues_list(request):
    """
    Shows leaderboard for current week.
    Simple version: Shows top 20 users by League XP.
    """
    g, _ = UserGamification.objects.get_or_create(user=request.user)
    
    # Filter users in same league
    # In real app, we would group by 'cohort' (random 30 users).
    # For now, global leaderboard per league tier.
    leaderboard = list(UserGamification.objects.filter(
        current_league=g.current_league
    ).select_related('user', 'user__profile').order_by('-league_xp')[:50])
    
    # Check if user is in leaderboard (leaderboard is now a list)
    user_in_leaderboard = any(u.user == request.user for u in leaderboard)
    
    return render(request, "pages/leagues.html", {
        "leaderboard": leaderboard,
        "my_league": g.get_current_league_display(),
        "user_gamification": g,
        "user_in_leaderboard": user_in_leaderboard
    })


@login_required
def shop_index(request):
    """
    Item shop (Streak Freeze, Heart Refill, etc)
    """
    g, _ = UserGamification.objects.get_or_create(user=request.user)
    return render(request, "pages/shop.html", {"game": g})


@login_required
def shop_purchase(request, item):
    """
    Handle shop purchases:
    - streak_freeze: 200 XP
    - hearts: 300 XP
    """
    g, _ = UserGamification.objects.get_or_create(user=request.user)
    
    if request.method == "POST":
        if item == "streak_freeze":
            cost = 200
            if g.xp_total >= cost and g.streak_freeze_count == 0:
                g.xp_total -= cost
                g.streak_freeze_count += 1
                g.save()
                messages.success(request, "Streak Freeze sotib olindi! 🎉")
            elif g.streak_freeze_count > 0:
                messages.warning(request, "Sizda allaqachon Streak Freeze bor.")
            else:
                messages.error(request, f"Yetarli XP yo'q. Kerak: {cost} XP")
                
        elif item == "hearts":
            cost = 300
            if g.xp_total >= cost:
                g.xp_total -= cost
                g.hearts = 5  # Full refill
                g.save()
                messages.success(request, "Jonlar to'ldirildi! ❤️")
            else:
                messages.error(request, f"Yetarli XP yo'q. Kerak: {cost} XP")
    
    return redirect("arab:shop_index")


@login_required
@require_POST
def save_push_subscription(request):
    try:
        data = json.loads(request.body)
        reminder, _ = UserReminder.objects.get_or_create(user=request.user)
        reminder.push_subscription = data
        reminder.save()
        return JsonResponse({'status': 'ok'})
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=400)

@login_required
def feedback_view(request):
    if request.method == 'POST':
        form = FeedbackForm(request.POST)
        if form.is_valid():
            feedback = form.save(commit=False)
            feedback.user = request.user
            feedback.save()
            messages.success(request, "Xabaringiz qabul qilindi! Tez orada ko'rib chiqamiz.")
            return redirect('arab:feedback')
    else:
        form = FeedbackForm()
    
    return render(request, "pages/feedback.html", {"form": form})

@login_required
@require_POST
def api_quiz_result(request):
    """
    Handle post-login daily quiz results.
    """
    try:
        data = json.loads(request.body)
        is_correct = data.get('correct', False)
        
        if is_correct:
            # Giving small XP reward
            g, _ = UserGamification.objects.get_or_create(user=request.user)
            g.xp_total += 10
            g.save()
            
        # Mark as taken placement test if not already done
        if hasattr(request.user, 'profile') and not request.user.profile.has_taken_placement_test:
            request.user.profile.has_taken_placement_test = True
            request.user.profile.save()
            
        return JsonResponse({'status': 'ok', 'xp_added': 10 if is_correct else 0})
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=400)


@login_required
def exam_view(request):
    """
    Arabic exam/test page (mock version).
    """
    return render(request, "exam/index.html")
