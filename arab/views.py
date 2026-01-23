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

try:
    import face_recognition
except ImportError:
    face_recognition = None

try:
    import numpy as np
except ImportError:
    np = None

import base64
import json
import io

try:
    from PIL import Image
except ImportError:
    Image = None

from .forms import LoginForm, RegisterForm, UserUpdateForm, ProfileUpdateForm
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
    QuranSurah,
    QuranAyah,
    Mission,
    UserMissionProgress
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
        return (s.reviews_done >= 10) or (s.lessons_done >= 1) or (s.new_words >= 5) or (s.study_minutes >= 15)

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
    
    # Save to DB
    UserStreak.objects.update_or_create(
        user=user, 
        defaults={"current_streak": cur, "best_streak": best}
    )

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


def _get_daily_missions(user):
    """
    Get or create 3 daily missions for the user.
    """
    today = timezone.localdate()
    # Check if we have missions for today
    existing = UserMissionProgress.objects.filter(user=user, date=today).select_related("mission")
    if existing.count() >= 3:
        return existing

    # Create new missions if not enough
    # If no Mission templates exist, create some defaults
    if Mission.objects.count() == 0:
        Mission.objects.create(title="Review 10 ta so'z", mission_type="review", required_count=10, xp_reward=15)
        Mission.objects.create(title="Review 20 ta so'z", mission_type="review", required_count=20, xp_reward=25)
        Mission.objects.create(title="1 ta dars tugat", mission_type="lesson", required_count=1, xp_reward=50)
        Mission.objects.create(title="5 ta yangi so'z", mission_type="word", required_count=5, xp_reward=20)
        Mission.objects.create(title="15 daqiqa shug'ullan", mission_type="time", required_count=15, xp_reward=30)

    # Pick 3 random missions
    all_missions = list(Mission.objects.all())
    # Try to pick different types if possible
    selected_missions = random.sample(all_missions, k=min(3, len(all_missions)))
    
    # Check current progress from DailyStat (to sync initial state if user did actions before generating missions)
    stat = UserDailyStat.objects.filter(user=user, day=today).first()
    
    new_progs = []
    for m in selected_missions:
        # Check if already assigned
        if not UserMissionProgress.objects.filter(user=user, mission=m, date=today).exists():
            # Init progress based on DailyStat
            current = 0
            if stat:
                if m.mission_type == "review": current = stat.reviews_done
                elif m.mission_type == "lesson": current = stat.lessons_done
                elif m.mission_type == "word": current = stat.new_words
                elif m.mission_type == "time": current = stat.study_minutes
            
            is_done = current >= m.required_count
            mp = UserMissionProgress.objects.create(
                user=user, 
                mission=m, 
                date=today,
                current_progress=min(current, m.required_count),
                is_completed=is_done
            )
            if is_done:
                # Award XP immediately if auto-completed
                g, _ = UserGamification.objects.get_or_create(user=user)
                g.xp_total += m.xp_reward
                g.save()
                
            new_progs.append(mp)
            
    # Re-fetch all to return uniform queryset
    return UserMissionProgress.objects.filter(user=user, date=today).select_related("mission")


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
        UserWeakArea.objects.create(
            user=user,
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
    return render(request, "tajweed/whiteboard.html")


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
    active_users = UserGamification.objects.filter(xp_total__gt=0).count() + 120 # simulated + real
    
    context = {
        "total_words": total_words,
        "total_letters": total_letters,
        "active_users": active_users,
    }
    
    if request.user.is_authenticated:
        g, _ = UserGamification.objects.get_or_create(user=request.user)
        context["game"] = g
        context["streak"] = _calc_streak(request.user)
        
        # Next Lesson logic
        from .models import UserLessonProgress, Lesson
        last_progress = UserLessonProgress.objects.filter(user=request.user).order_by("-updated_at").first()
        if last_progress:
            # Simple logic: next lesson in the same unit or next unit
            next_lesson = Lesson.objects.filter(
                unit=last_progress.lesson.unit, 
                order__gt=last_progress.lesson.order
            ).order_by("order").first()
            
            if not next_lesson:
                # Try next unit
                next_unit = last_progress.lesson.unit.course.units.filter(
                    order__gt=last_progress.lesson.unit.order
                ).order_by("order").first()
                if next_unit:
                    next_lesson = next_unit.lessons.order_by("order").first()
            
            context["next_lesson"] = next_lesson
        else:
            # Pick first lesson of first course
            context["next_lesson"] = Lesson.objects.filter(unit__course__is_published=True).order_by("unit__course__level", "unit__order", "order").first()

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
    examples = list(letter.examples.all()[:3])

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
    return render(request, "alphabet/practice.html", {"letter": letter})


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

    return render(request, "courses/detail.html", {"course": course, "units": units})


@login_required
def lesson_detail(request, pk):
    lesson = get_object_or_404(Lesson, pk=pk)

    # Locking logic (Prev lesson completion)
    prev = Lesson.objects.filter(unit=lesson.unit, order__lt=lesson.order).order_by("-order").first()
    if prev:
        if not UserLessonProgress.objects.filter(user=request.user, lesson=prev, is_completed=True).exists():
             return render(request, "pages/locked.html")

    return render(request, "lessons/detail.html", {"lesson": lesson})


@login_required
def video_detail(request, pk):
    video = get_object_or_404(LessonVideo, pk=pk)
    
    # Progress check
    prog, _ = UserVideoProgress.objects.get_or_create(user=request.user, video=video)
    
    # Prev/Next logic could be added here
    
    return render(request, "lessons/video.html", {"video": video, "progress": prog})


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
    
    # Filter
    q = request.GET.get("q", "")
    if q:
        videos = videos.filter(title__icontains=q)
        
    return render(request, "lessons/library.html", {"videos": videos, "q": q})


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
    next_xp = xp_for_next_level(g.level)
    return JsonResponse({
        "xp": g.xp_total,
        "level": g.level,
        "next_level_xp": next_xp,
        "xp_pct": int((g.xp_total % next_xp / next_xp) * 100) if next_xp else 0
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


# ----------------------------
# PLACEMENT TEST
# ----------------------------
@login_required
def placement_test(request):
    if request.method == "POST":
        # Simple scoring logic for demo purposes
        score = 0
        # Answers key: q_id -> correct_option_index
        answers = {
            "1": "0", # Alif
            "2": "1", # 28
            "3": "0", # Right to Left
            "4": "2", # Salam
            "5": "0", # Kitab
        }
        
        for q_id, correct_val in answers.items():
            if request.POST.get(f"q_{q_id}") == correct_val:
                score += 1
                
        # Determine level
        if score <= 2:
            level = 1 # A0
            msg = "Boshlang‘ich daraja (A0). Alifbodan boshlaymiz!"
        elif score <= 4:
            level = 2 # A1
            msg = "Yaxshi natija! (A1). So‘zlarni o‘rganishga o‘tamiz."
        else:
            level = 3 # A2
            msg = "Ajoyib! (A2). Grammatika va o‘qishni davom ettiramiz."
            
        g, _ = UserGamification.objects.get_or_create(user=request.user)
        g.level = level
        g.xp_total += score * 50 # Bonus XP
        g.save()
        
        # Unlock logic could go here (e.g. mark previous lessons as done)
        
        return render(request, "pages/placement_result.html", {"score": score, "level": level, "msg": msg})

    questions = [
        {
            "id": 1, 
            "text": "Arab alifbosidagi birinchi harf qaysi?", 
            "options": ["Alif (ا)", "Ba (ب)", "Jim (ج)"]
        },
        {
            "id": 2, 
            "text": "Arab alifbosida nechta harf bor?", 
            "options": ["26", "28", "32"]
        },
        {
            "id": 3, 
            "text": "Arab yozuvi qaysi tomondan yoziladi?", 
            "options": ["O‘ngdan chapga", "Chapdan o‘ngga", "Tepadan pastga"]
        },
        {
            "id": 4, 
            "text": "'Salom' arab tilida qanday aytiladi?", 
            "options": ["Marhaban", "Shukran", "Assalamu alaykum"]
        },
        {
            "id": 5, 
            "text": "'Kitob' so‘zining arabchasi?", 
            "options": ["Kitab (كتاب)", "Qalam (قلم)", "Bab (باب)"]
        },
    ]
    return render(request, "pages/placement.html", {"questions": questions})


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
            Q(translation_uz__icontains=q) |
            Q(translation_ru__icontains=q)
        )

    if cat:
        words = words.filter(category__name__iexact=cat)
        
    if alpha:
        if alpha.isalpha(): # Latin or generic alpha
            words = words.filter(transliteration__istartswith=alpha)
        else: # Likely Arabic
            words = words.filter(arabic__startswith=alpha)

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
        card, created = UserWordProgress.objects.get_or_create(
            user=request.user,
            word=word,
            defaults={'level': 0, 'next_review': timezone.now()}
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
            user = form.save()
            
            # --- Inline Face Setup ---
            face_data = request.POST.get("face_data")
            if face_data:
                # Reuse OpenCV helper
                face_hist = get_face_data_from_base64(face_data)
                if face_hist is not None:
                    profile = user.profile
                    profile.face_encoding = json.dumps(face_hist)
                    profile.save()
            # -------------------------

            login(request, user)
            return redirect("arab:progress")
    else:
        form = RegisterForm()

    return render(request, "auth/register.html", {"form": form})


def login_view(request):
    if request.user.is_authenticated:
        return redirect("arab:progress")

    error = ""
    if request.method == "POST":
        form = LoginForm(request.POST)
        if form.is_valid():
            user = authenticate(
                request,
                username=form.cleaned_data["username"],
                password=form.cleaned_data["password"],
            )
            if user:
                login(request, user)
                return redirect("arab:progress")
            error = "Login yoki parol noto‘g‘ri."
    else:
        form = LoginForm()

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

    # Due count
    due_count = 0

    # Words
    learned_words = UserDailyStat.objects.filter(user=user).aggregate(s=Sum("new_words"))["s"] or 0
    total_words = 500
    words_pct = int((learned_words / max(1, total_words)) * 100)

    # Lessons
    lessons_completed = UserDailyStat.objects.filter(user=user).aggregate(s=Sum("lessons_done"))["s"] or 0
    lessons_total = 60
    lessons_pct = int((lessons_completed / max(1, lessons_total)) * 100)

    # Gamification
    g, _ = UserGamification.objects.get_or_create(user=user)
    level = g.level
    xp = g.xp_total
    xp_next = xp_for_next_level(level)
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
    for _w in range(10):
        row = []
        for _d in range(7):
            st = stats_map.get(cur)
            row.append(intensity(st))
            cur += timedelta(days=1)
    heatmap = []
    cur = start_day
    for _w in range(10):
        row = []
        for _d in range(7):
            st = stats_map.get(cur)
            row.append(intensity(st))
            cur += timedelta(days=1)
        heatmap.append(row)

    # Missions
    missions = _get_daily_missions(user)

    context = {
        "streak": streak,
        "due_count": due_count,
        "learned_words": learned_words,
        "total_words": total_words,
        "words_pct": words_pct,
        "lessons_completed": lessons_completed,
        "lessons_total": lessons_total,
        "lessons_pct": lessons_pct,
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
        "rank_name": "Bronze" if xp < 500 else "Silver" if xp < 1000 else "Gold",
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
    # Ensure profile exists for existing users
    profile, created = Profile.objects.get_or_create(user=request.user)
    
    if request.method == 'POST':
        u_form = UserUpdateForm(request.POST, instance=request.user)
        p_form = ProfileUpdateForm(request.POST, request.FILES, instance=profile)
        if u_form.is_valid() and p_form.is_valid():
            u_form.save()
            p_form.save()
            messages.success(request, f'Profilingiz muvaffaqiyatli yangilandi!')
            return redirect('arab:settings_profile')
    else:
        u_form = UserUpdateForm(instance=request.user)
        p_form = ProfileUpdateForm(instance=profile)

    context = {
        'u_form': u_form,
        'p_form': p_form
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
# FACE AUTH (OpenCV-based)
# ----------------------------
import cv2

def get_face_data_from_base64(base64_string):
    """Extract face region and compute histogram for comparison"""
    if np is None:
        return None
        
    try:
        if "base64," in base64_string:
            base64_string = base64_string.split("base64,")[1]
        
        image_data = base64.b64decode(base64_string)
        nparr = np.frombuffer(image_data, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        if img is None:
            return None
        
        # Convert to grayscale for face detection
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        
        # Load Haar Cascade for face detection
        cascade_path = cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
        face_cascade = cv2.CascadeClassifier(cascade_path)
        
        faces = face_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5, minSize=(80, 80))
        
        if len(faces) == 0:
            return None
        
        # Get the largest face
        x, y, w, h = max(faces, key=lambda f: f[2] * f[3])
        face_roi = gray[y:y+h, x:x+w]
        
        # Resize to standard size for comparison
        face_resized = cv2.resize(face_roi, (100, 100))
        
        # Compute histogram as "encoding"
        hist = cv2.calcHist([face_resized], [0], None, [256], [0, 256])
        cv2.normalize(hist, hist)
        
        return hist.flatten().tolist()
        
    except Exception as e:
        print(f"Face Error: {e}")
        return None

def compare_face_histograms(hist1, hist2, threshold=0.7):
    """Compare two face histograms using correlation"""
    if np is None:
        return False
    try:
        h1 = np.array(hist1, dtype=np.float32)
        h2 = np.array(hist2, dtype=np.float32)
        correlation = cv2.compareHist(h1, h2, cv2.HISTCMP_CORREL)
        return correlation > threshold
    except:
        return False

@login_required
def face_setup(request):
    if np is None:
        return JsonResponse({"success": False, "error": "Numpy kutubxonasi yuklanmadi..."})

    if request.method == "POST":
        try:
            data = json.loads(request.body)
            image_data = data.get("image")
            
            face_hist = get_face_data_from_base64(image_data)
            if face_hist is None:
                return JsonResponse({"success": False, "error": "Yuz aniqlanmadi. Iltimos yorug'roq joyda urinib ko'ring."})
                
            # Save face histogram
            profile = request.user.profile
            profile.face_encoding = json.dumps(face_hist)
            profile.save()
            
            return JsonResponse({"success": True})
        except Exception as e:
            return JsonResponse({"success": False, "error": str(e)})
        
    return render(request, "registration/face_setup.html")

def face_login(request):
    if request.user.is_authenticated:
        return redirect("arab:progress")
    
    if np is None:
        if request.method == "POST":
            return JsonResponse({"success": False, "error": "Tizim hali tayyorlanmoqda..."})
        return render(request, "registration/face_login.html")

    if request.method == "POST":
        try:
            data = json.loads(request.body)
            image_data = data.get("image")
            
            unknown_hist = get_face_data_from_base64(image_data)
            if unknown_hist is None:
                return JsonResponse({"success": False, "error": "Yuz aniqlanmadi."})
                
            # Check against all users with face_encoding
            profiles = Profile.objects.exclude(face_encoding__isnull=True).exclude(face_encoding="")
            
            found_user = None
            for p in profiles:
                try:
                    known_hist = json.loads(p.face_encoding)
                    if compare_face_histograms(known_hist, unknown_hist, threshold=0.6):
                        found_user = p.user
                        break
                except:
                    continue
            
            if found_user:
                login(request, found_user)
                return JsonResponse({"success": True, "redirect": "/progress/"})
            else:
                return JsonResponse({"success": False, "error": "Foydalanuvchi topilmadi."})
                
        except Exception as e:
            return JsonResponse({"success": False, "error": str(e)})
        
    return render(request, "registration/face_login.html")


# ----------------------------
# ERROR HANDLERS
# ----------------------------
def custom_404(request, exception):
    return render(request, "404.html", status=404)

def custom_500(request):
    return render(request, "500.html", status=500)
