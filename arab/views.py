from datetime import timedelta
import random

from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_http_methods, require_POST

from .forms import LoginForm, RegisterForm
from .models import (
    Course,
    Exercise,
    Lesson,
    Letter,
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
    Word,
)
from django.db.models import Sum
from .models import UserDailyStat, UserGamification, UserWeakArea
from .progress_tracking import xp_for_next_level


def _calc_streak(user) -> dict:
    """
    daily_stats asosida streak hisoblaydi (study/review/lesson/word bo'lsa activity hisoblanadi).
    """
    stats = UserDailyStat.objects.filter(user=user).order_by("-day")
    if not stats.exists():
        return {"current_streak": 0, "best_streak": 0}

    # best streak
    days = list(stats.values_list("day", "study_minutes", "reviews_done", "new_words", "lessons_done"))
    active_days = set()
    for d, sm, r, w, l in days:
        if (sm or 0) > 0 or (r or 0) > 0 or (w or 0) > 0 or (l or 0) > 0:
            active_days.add(d)

    def is_active(d):
        return d in active_days

    # current streak from today backwards
    today = timezone.localdate()
    cur = 0
    d = today
    while is_active(d):
        cur += 1
        d = d - timedelta(days=1)

    # best streak scan
    best = 0
    # sort ascending for scan
    sorted_days = sorted(active_days)
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

    return {"current_streak": cur, "best_streak": best}


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

    # Due count — sizda SRS modeli bo'lsa shu yerga ulaysiz.
    # Hozircha 0 fallback (keyin integratsiya qilamiz).
    due_count = 0

    # Words — sizda dictionary progress modeli bo'lsa shu yerga ulaysiz.
    # Hozircha daily_stats orqali umumiy yodlangan so'zlar:
    learned_words = UserDailyStat.objects.filter(user=user).aggregate(s=Sum("new_words"))["s"] or 0
    total_words = 500  # xohlasangiz DBdan real lug'at count qiling
    words_pct = int((learned_words / max(1, total_words)) * 100)

    # Lessons — sizda lesson completion bo'lsa shu yerga ulaysiz.
    lessons_completed = UserDailyStat.objects.filter(user=user).aggregate(s=Sum("lessons_done"))["s"] or 0
    lessons_total = 60  # kurslar/darslar soni
    lessons_pct = int((lessons_completed / max(1, lessons_total)) * 100)

    # Gamification
    g, _ = UserGamification.objects.get_or_create(user=user)
    level = g.level
    xp = g.xp_total
    xp_next = xp_for_next_level(level)
    # xp_pct: umumiy xp_totalni threshold ga bo'lish emas, UX uchun "level progress" sifatida ko'rsatamiz:
    # bu soddalashtirilgan: xp_total % xp_next
    xp_in_level = xp % xp_next
    xp_pct = int((xp_in_level / max(1, xp_next)) * 100)
    xp_remaining = max(0, xp_next - xp_in_level)

    # Study time
    week_start = today - timedelta(days=6)
    last7 = list(UserDailyStat.objects.filter(user=user, day__gte=week_start, day__lte=today).order_by("day"))
    study_today_min = today_stat.study_minutes
    study_week_min = sum(x.study_minutes for x in last7)
    study_avg_min = int(study_week_min / 7)

    # Weekly bars (7 kunlik)
    # "actions" = review + new_words + lessons (xohlasangiz minutes ham qo'shing)
    week_total_actions = 0
    week_bars = []
    for s in last7:
        actions = (s.reviews_done or 0) + (s.new_words or 0) + (s.lessons_done or 0)
        week_total_actions += actions
        week_bars.append({"label": s.day.strftime("%a"), "raw": actions})

    max_actions = max([b["raw"] for b in week_bars], default=0)
    for b in week_bars:
        b["pct"] = int((b["raw"] / max(1, max_actions)) * 100) if max_actions else 0

    # Recommendations (next actions)
    recommendations = []
    if due_count > 0:
        recommendations.append({"title": "Review qil", "desc": f"{due_count} ta card kutyapti", "url": "/review/"})
    if lessons_completed < lessons_total:
        recommendations.append({"title": "Kurs davom et", "desc": "1 ta dars tugat", "url": "/courses/"})
    if learned_words < total_words:
        recommendations.append({"title": "5 ta yangi so‘z", "desc": "Lug‘atdan o‘rgan", "url": "/dictionary/"})
    if not recommendations:
        recommendations.append({"title": "Practice", "desc": "10 daqiqa mashq qil", "url": "/practice/"})

    # Achievements (badge’lar)
    achievements = []
    if streak["current_streak"] >= 3:
        achievements.append({"icon": "🔥", "title": "3-day streak"})
    if streak["current_streak"] >= 7:
        achievements.append({"icon": "🔥", "title": "7-day streak"})
    if learned_words >= 50:
        achievements.append({"icon": "📚", "title": "50 ta so‘z"})
    if learned_words >= 200:
        achievements.append({"icon": "📚", "title": "200 ta so‘z"})
    if lessons_completed >= 10:
        achievements.append({"icon": "🎓", "title": "10 ta dars"})
    if lessons_completed >= 30:
        achievements.append({"icon": "🎓", "title": "30 ta dars"})
    if xp >= 500:
        achievements.append({"icon": "🧩", "title": "500 XP"})
    if xp >= 1000:
        achievements.append({"icon": "🧩", "title": "1000 XP"})

    # Weak areas (DBdan)
    weak_areas_qs = UserWeakArea.objects.filter(user=user).order_by("pct")[:3]
    weak_areas = [{"title": w.title, "pct": w.pct, "url": w.url} for w in weak_areas_qs]

    # Heatmap (GitHub style)
    # 10 hafta x 7 kun (70 kun)
    days_back = 70
    start_day = today - timedelta(days=days_back - 1)

    stats_map = {
        s.day: s for s in UserDailyStat.objects.filter(user=user, day__gte=start_day, day__lte=today)
    }

    def intensity(s: UserDailyStat | None) -> float:
        if not s:
            return 0.05
        score = (s.reviews_done or 0) + (s.new_words or 0) * 2 + (s.lessons_done or 0) * 5 + (s.study_minutes or 0) * 0.1
        # score -> opacity 0.08..0.90
        if score <= 0:
            return 0.05
        if score < 5:
            return 0.18
        if score < 15:
            return 0.35
        if score < 30:
            return 0.55
        return 0.85

    heatmap = []
    cur = start_day
    # 10 week
    for _w in range(10):
        row = []
        for _d in range(7):
            st = stats_map.get(cur)
            row.append(intensity(st))
            cur += timedelta(days=1)
        heatmap.append(row)

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

        "recommendations": recommendations,
        "achievements": achievements,
        "weak_areas": weak_areas,
        "heatmap": heatmap,
    }
    return render(request, "progress.html", context)


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

    return render(
        request,
        "tajweed/index.html",
        {"rules": rules.order_by("level", "title"), "q": q, "level": level, "levels": levels},
    )


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
    return render(request, "pages/home.html")


def roadmap(request):
    levels = ["A0", "A1", "A2", "B1"]
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


def course_detail(request, pk):
    course = get_object_or_404(Course, pk=pk)
    units = course.units.prefetch_related("lessons").all()
    return render(request, "courses/detail.html", {"course": course, "units": units})


def lesson_detail(request, pk):
    lesson = get_object_or_404(Lesson, pk=pk)
    return render(request, "lessons/detail.html", {"lesson": lesson})


# ----------------------------
# PRACTICE
# ----------------------------
def practice_hub(request):
    return render(request, "practice/index.html")


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

    return redirect("arab:review")


# ----------------------------
# DICTIONARY
# ----------------------------
def dictionary(request):
    q = request.GET.get("q", "").strip()
    cat = request.GET.get("cat", "").strip()

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

    words = words.order_by("arabic")[:200]

    return render(request, "dictionary/index.html", {"words": words, "q": q, "cat": cat})


# ----------------------------
# PROGRESS
# ----------------------------
@login_required
def progress(request):
    streak, _ = UserStreak.objects.get_or_create(user=request.user)

    total_words = Word.objects.count()
    learned_words = UserWordProgress.objects.filter(user=request.user, strength__gte=60).count()

    lessons_total = Lesson.objects.count()
    lessons_completed = UserLessonProgress.objects.filter(user=request.user, is_completed=True).count()

    due_count = UserCard.objects.filter(user=request.user, due_at__lte=timezone.now()).count()

    words_pct = int((learned_words / total_words) * 100) if total_words else 0
    lessons_pct = int((lessons_completed / lessons_total) * 100) if lessons_total else 0

    return render(request, "progress/index.html", {
        "streak": streak,
        "total_words": total_words,
        "learned_words": learned_words,
        "words_pct": words_pct,
        "lessons_total": lessons_total,
        "lessons_completed": lessons_completed,
        "lessons_pct": lessons_pct,
        "due_count": due_count,
    })


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
def logout_view(request):
    logout(request)
    return redirect("arab:home")
