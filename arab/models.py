from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Q
from django.utils import timezone


# ----------------------------
# QURAN
# ----------------------------
class QuranSurah(models.Model):
    number = models.PositiveIntegerField(primary_key=True)  # 1..114
    name = models.CharField(max_length=100)  # Fatiha
    english_name = models.CharField(max_length=100)  # The Opening
    ayah_count = models.PositiveIntegerField()
    place = models.CharField(max_length=20, choices=[("Mecca", "Mecca"), ("Medina", "Medina")], default="Mecca")

    class Meta:
        ordering = ["number"]

    def __str__(self):
        return f"{self.number}. {self.name}"


class QuranAyah(models.Model):
    surah = models.ForeignKey(QuranSurah, on_delete=models.CASCADE, related_name="ayahs")
    number_in_surah = models.PositiveIntegerField()
    text = models.TextField()  # Arabic text (Uthmani)
    audio = models.FileField(upload_to="audio/quran/", blank=True, null=True)

    class Meta:
        ordering = ["surah", "number_in_surah"]
        unique_together = ("surah", "number_in_surah")

    def __str__(self):
        return f"{self.surah.name}:{self.number_in_surah}"


# ----------------------------
# BASE
# ----------------------------
class TimeStamped(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


# ----------------------------
# COURSES
# ----------------------------
class Course(TimeStamped):
    LEVEL_CHOICES = [("A0", "A0"), ("A1", "A1"), ("A2", "A2"), ("B1", "B1")]

    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    level = models.CharField(max_length=30, choices=LEVEL_CHOICES, default="A0")
    image = models.ImageField(upload_to="courses/", blank=True, null=True)
    is_published = models.BooleanField(default=False)

    class Meta:
        ordering = ["level", "id"]

    def __str__(self):
        return f"{self.title} ({self.level})"


class Unit(TimeStamped):
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name="units")
    title = models.CharField(max_length=200)
    order = models.PositiveIntegerField(default=1)

    class Meta:
        ordering = ["order"]
        constraints = [
            models.UniqueConstraint(fields=["course", "order"], name="uniq_unit_order_in_course"),
        ]

    def __str__(self):
        return f"{self.course.title} / {self.title}"


class Lesson(TimeStamped):
    unit = models.ForeignKey(Unit, on_delete=models.CASCADE, related_name="lessons")
    title = models.CharField(max_length=200)
    theory = models.TextField(blank=True)
    order = models.PositiveIntegerField(default=1)
    estimated_minutes = models.PositiveIntegerField(default=10)
    
    # Advanced: Sequence of mini-blocks
    # [ {"type": "intro", "content": "..."}, {"type": "vocabulary", "word_ids": [1,2,3]}, ... ]
    blocks = models.JSONField(default=list, blank=True, help_text="Lesson mini-bloklar ketma-ketligi")

    class Meta:
        ordering = ["order"]
        constraints = [
            models.UniqueConstraint(fields=["unit", "order"], name="uniq_lesson_order_in_unit"),
        ]

    def __str__(self):
        return f"{self.unit.title} / {self.title}"


class LessonSection(TimeStamped):
    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE, related_name="sections")
    title = models.CharField(max_length=200)
    content = models.TextField()
    order = models.PositiveIntegerField(default=1)

    class Meta:
        ordering = ["order"]
        constraints = [
            models.UniqueConstraint(fields=["lesson", "order"], name="uniq_section_order_in_lesson"),
        ]

    def __str__(self):
        return f"{self.lesson.title} / {self.title}"


# ----------------------------
# ALPHABET
# ----------------------------
class Letter(TimeStamped):
    name = models.CharField(max_length=50)                  # Alif
    arabic = models.CharField(max_length=5, unique=True)    # ا
    order = models.PositiveIntegerField(unique=True)        # 1..28
    abjad_value = models.PositiveIntegerField(null=True, blank=True)

    isolated = models.CharField(max_length=5, blank=True)
    initial = models.CharField(max_length=5, blank=True)
    medial = models.CharField(max_length=5, blank=True)
    final = models.CharField(max_length=5, blank=True)

    joins_to_next = models.BooleanField(default=True)


    # Makhraj info
    makhraj_image = models.ImageField(upload_to="makhraj/", blank=True, null=True, help_text="Image showing articulation point")
    makhraj_description = models.TextField(blank=True, help_text="Description of articulation mechanism")

    # Animation
    svg_path = models.TextField(blank=True, help_text="SVG d atributi (stroke animatsiyasi uchun)")
    viewbox = models.CharField(max_length=50, default="0 0 100 100", help_text="SVG viewbox o'lchami")

    class Meta:
        ordering = ["order"]

    def __str__(self):
        return f"{self.name} ({self.arabic})"


class Pronunciation(TimeStamped):
    letter = models.ForeignKey(Letter, on_delete=models.CASCADE, related_name="pronunciations")
    description = models.TextField(blank=True)
    audio = models.FileField(upload_to="audio/letters/", blank=True, null=True)

    def __str__(self):
        return f"Pronunciation: {self.letter.arabic}"


class LetterExample(TimeStamped):
    letter = models.ForeignKey(Letter, on_delete=models.CASCADE, related_name="examples")
    arabic_text = models.CharField(max_length=120)
    transliteration = models.CharField(max_length=120, blank=True)
    translation_uz = models.CharField(max_length=200, blank=True)
    audio = models.FileField(upload_to="audio/letter_examples/", blank=True, null=True)

    class Meta:
        ordering = ["id"]

    def __str__(self):
        return f"{self.letter.arabic}: {self.arabic_text}"


# ----------------------------
# DIACRITICS / GRAMMAR
# ----------------------------
class Diacritic(TimeStamped):
    KEY_CHOICES = [
        ("FATHA", "Fatha"),
        ("KASRA", "Kasra"),
        ("DAMMA", "Damma"),
        ("SUKUN", "Sukun"),
        ("SHADDA", "Shadda"),
        ("TANWIN_DAMMA", "Tanwin Damma (-un)"),
        ("TANWIN_KASRA", "Tanwin Kasra (-in)"),
        ("TANWIN_FATHA", "Tanwin Fatha (-an)"),
    ]
    key = models.CharField(max_length=20, choices=KEY_CHOICES, unique=True)
    symbol = models.CharField(max_length=5)
    description = models.CharField(max_length=255, blank=True)

    class Meta:
        ordering = ["key"]

    def __str__(self):
        return f"{self.get_key_display()} {self.symbol}"


class GrammarRule(TimeStamped):
    title = models.CharField(max_length=200)
    explanation = models.TextField()
    examples = models.JSONField(default=list, blank=True)
    related_diacritics = models.ManyToManyField(Diacritic, blank=True, related_name="grammar_rules")

    def __str__(self):
        return self.title


# ----------------------------
# VOCABULARY
# ----------------------------
class VocabularyCategory(TimeStamped):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)

    def __str__(self):
        return self.name


class Word(TimeStamped):
    lesson = models.ForeignKey(Lesson, on_delete=models.SET_NULL, null=True, blank=True, related_name="words")
    arabic = models.CharField(max_length=100, unique=True, error_messages={'unique': "Bu so'z allaqachon mavjud!"})
    transliteration = models.CharField(max_length=150, blank=True)
    pronunciation = models.CharField(max_length=200, blank=True, help_text="O'qilishi (O'zbek lofida)")
    makhraj = models.TextField(blank=True, help_text="Talaffuz o'rni (maxraj)")
    translation_uz = models.CharField(max_length=200, blank=True)
    translation_ru = models.CharField(max_length=200, blank=True)
    word_type = models.CharField(max_length=50, blank=True, help_text="So'z turkumi (Ot, Sifat, va h.k.)")
    
    DIFFICULTY_CHOICES = [
        ("easy", "Oson"),
        ("medium", "O'rtacha"),
        ("hard", "Qiyin"),
    ]
    difficulty = models.CharField(max_length=20, choices=DIFFICULTY_CHOICES, default="easy")

    category = models.ForeignKey(
        VocabularyCategory,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="words",
    )

    diacritics = models.ManyToManyField(Diacritic, blank=True, related_name="words")
    audio = models.FileField(upload_to="audio/words/", blank=True, null=True)

    class Meta:
        ordering = ["arabic"]
        indexes = [models.Index(fields=["arabic"])]

    def __str__(self):
        return self.arabic


class WordExample(TimeStamped):
    word = models.ForeignKey(Word, on_delete=models.CASCADE, related_name="examples")
    arabic_text = models.CharField(max_length=255)
    translation_uz = models.CharField(max_length=255, blank=True)
    audio = models.FileField(upload_to="audio/word_examples/", blank=True, null=True)

    def __str__(self):
        return f"{self.word.arabic} → {self.arabic_text}"


# ----------------------------
# EXERCISES
# ----------------------------
class Exercise(TimeStamped):
    TYPE_CHOICES = [
        ("READ", "O‘qish"),
        ("WRITE", "Yozish"),
        ("LISTEN", "Tinglab tanlash"),
        ("QUIZ", "Test"),
        ("COMBO", "Harf + harakat"),
    ]
    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE, related_name="exercises")
    title = models.CharField(max_length=200)
    type = models.CharField(max_length=10, choices=TYPE_CHOICES)
    instruction = models.TextField(blank=True)
    content = models.JSONField(default=dict, blank=True)

    def __str__(self):
        return f"{self.lesson.title} — {self.title}"


class Question(TimeStamped):
    exercise = models.ForeignKey(Exercise, on_delete=models.CASCADE, related_name="questions")
    text = models.TextField()
    audio = models.FileField(upload_to="audio/questions/", blank=True, null=True)
    explanation = models.TextField(blank=True)

    def __str__(self):
        return self.text[:60]


class Choice(TimeStamped):
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name="choices")
    text = models.CharField(max_length=200)
    is_correct = models.BooleanField(default=False)

    def __str__(self):
        return self.text


# ----------------------------
# USER PROGRESS
# ----------------------------
class UserLessonProgress(TimeStamped):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="lesson_progress")
    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE, related_name="user_progress")
    is_completed = models.BooleanField(default=False)
    percent = models.PositiveIntegerField(default=0)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["user", "lesson"], name="uniq_user_lesson_progress"),
        ]


class UserWordProgress(TimeStamped):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="word_progress")
    word = models.ForeignKey(Word, on_delete=models.CASCADE, related_name="user_progress")
    strength = models.PositiveIntegerField(default=0)  # 0..100
    last_seen = models.DateTimeField(null=True, blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["user", "word"], name="uniq_user_word_progress"),
        ]


class UserQuizAttempt(TimeStamped):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="quiz_attempts")
    exercise = models.ForeignKey(Exercise, on_delete=models.CASCADE, related_name="attempts")
    score = models.PositiveIntegerField(default=0)
    total = models.PositiveIntegerField(default=0)
    details = models.JSONField(default=dict, blank=True)


# ----------------------------
# SPACED REPETITION (REVIEW)
# ----------------------------
class UserCard(TimeStamped):
    """
    SM-2 uchun karta.
    Karta Word yoki Letter’dan faqat bittasiga bog‘lanadi.
    """
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="cards")

    word = models.ForeignKey(Word, on_delete=models.CASCADE, null=True, blank=True, related_name="cards")
    letter = models.ForeignKey(Letter, on_delete=models.CASCADE, null=True, blank=True, related_name="cards")

    repetitions = models.PositiveIntegerField(default=0)
    interval_days = models.PositiveIntegerField(default=0)
    ease_factor = models.FloatField(default=2.5)
    due_at = models.DateTimeField(default=timezone.now)

    class Meta:
        indexes = [models.Index(fields=["user", "due_at"])]
        constraints = [
            models.CheckConstraint(
                condition=(
                    (models.Q(word__isnull=False) & models.Q(letter__isnull=True)) |
                    (models.Q(word__isnull=True) & models.Q(letter__isnull=False))
                ),
                name="usercard_exactly_one_target"
            ),
            models.UniqueConstraint(fields=["user", "word"], name="uniq_user_word_card", condition=models.Q(word__isnull=False)),
            models.UniqueConstraint(fields=["user", "letter"], name="uniq_user_letter_card", condition=models.Q(letter__isnull=False)),
        ]

# ----------------------------
# PLACEMENT TEST
# ----------------------------
class PlacementQuestion(models.Model):
    text = models.TextField()
    audio = models.FileField(upload_to="audio/placement/", blank=True, null=True)
    level_tag = models.CharField(max_length=20, default="A0") # Recommended level if passed
    
class PlacementOption(models.Model):
    question = models.ForeignKey(PlacementQuestion, on_delete=models.CASCADE, related_name="options")
    text = models.CharField(max_length=200)
    is_correct = models.BooleanField(default=False)

    def __str__(self):
        return self.text


# ----------------------------
# STREAK / ACHIEVEMENTS
# ----------------------------
class UserStreak(TimeStamped):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="streak")
    current_streak = models.PositiveIntegerField(default=0)
    best_streak = models.PositiveIntegerField(default=0)


class Achievement(TimeStamped):
    title = models.CharField(max_length=100)
    description = models.TextField()
    icon = models.CharField(max_length=50, blank=True)

    def __str__(self):
        return self.title


class UserAchievement(TimeStamped):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="achievements")
    achievement = models.ForeignKey(Achievement, on_delete=models.CASCADE, related_name="users")
    earned_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["user", "achievement"], name="uniq_user_achievement"),
        ]


# ----------------------------
# TAJWEED
# ----------------------------
class TajweedRule(TimeStamped):
    CATEGORY_CHOICES = [
        ("alphabet", "Harflar va Maxraj"),
        ("noon_sakinah", "Noon Sakinah va Tanween"),
        ("meem_sakinah", "Meem Sakinah"),
        ("mudood", "Muddood (Cho'ziqlar)"),
        ("sifat", "Harf Sifatlari"),
        ("other", "Boshqa qoidalar"),
    ]

    slug = models.SlugField(unique=True)
    title = models.CharField(max_length=200)
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES, default="other")
    short_desc = models.CharField(max_length=255, blank=True)
    explanation = models.TextField()
    level = models.CharField(
        max_length=10,
        choices=[("A0", "A0"), ("A1", "A1"), ("A2", "A2"), ("B1", "B1")],
        default="A0",
    )
    is_published = models.BooleanField(default=True)

    class Meta:
        ordering = ["level", "title"]

    def __str__(self):
        return self.title


class TajweedExample(TimeStamped):
    rule = models.ForeignKey(TajweedRule, on_delete=models.CASCADE, related_name="examples")
    arabic_text = models.TextField()
    translation_uz = models.TextField(blank=True)
    transliteration = models.CharField(max_length=255, blank=True)
    description = models.TextField(blank=True, help_text="Qoida qanday qo'llanilishi haqida izoh")
    audio = models.FileField(upload_to="audio/tajweed/", blank=True, null=True)

    def __str__(self):
        return f"{self.rule.title} example #{self.pk}"


class TajweedTag(TimeStamped):
    name = models.CharField(max_length=100, unique=True)
    color = models.CharField(max_length=30, default="emerald")

    def __str__(self):
        return self.name


class TajweedMark(TimeStamped):
    """
    Misol ichidagi segment(lar)ni highlight qilish va taglash.
    start/end - arabic_text ichida indekslar: [start:end]
    """
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="tajweed_marks"
    )
    example = models.ForeignKey(TajweedExample, on_delete=models.CASCADE, related_name="marks")
    rule = models.ForeignKey(TajweedRule, on_delete=models.CASCADE, related_name="marks")
    tag = models.ForeignKey(TajweedTag, on_delete=models.SET_NULL, null=True, blank=True, related_name="marks")

    start = models.PositiveIntegerField()
    end = models.PositiveIntegerField()
    note = models.CharField(max_length=255, blank=True)

    class Meta:
        ordering = ["start", "end"]
        indexes = [
            models.Index(fields=["example", "start", "end"]),
            models.Index(fields=["rule"]),
            models.Index(fields=["tag"]),
        ]

    def clean(self):
        if self.end <= self.start:
            raise ValidationError("end start dan katta bo‘lishi kerak.")
        if self.example_id and self.example.arabic_text:
            n = len(self.example.arabic_text)
            if self.start >= n or self.end > n:
                raise ValidationError(f"Mark indexlar matn uzunligidan chiqib ketgan. (0..{n})")

    def __str__(self):
        return f"{self.rule.title} [{self.start}:{self.end}]"


class TajweedProgress(TimeStamped):
    """
    User qaysi qoidani tugatganini belgilash.
    """
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    rule = models.ForeignKey(TajweedRule, on_delete=models.CASCADE)
    completed = models.BooleanField(default=False)
    score = models.PositiveIntegerField(default=0)  # quiz natija (0-100)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["user", "rule"], name="uniq_user_rule_progress"),
        ]

    def __str__(self):
        return f"{self.user} - {self.rule} ({'done' if self.completed else 'todo'})"


class TajweedQuiz(TimeStamped):
    """
    Bitta savol: qaysi qoida?
    """
    rule = models.ForeignKey(TajweedRule, on_delete=models.CASCADE, related_name="quizzes")
    prompt = models.CharField(max_length=255)  # Savol matni (UZ)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"Quiz: {self.rule.title}"


class TajweedQuizOption(TimeStamped):
    quiz = models.ForeignKey(TajweedQuiz, on_delete=models.CASCADE, related_name="options")
    text = models.CharField(max_length=120)
    is_correct = models.BooleanField(default=False)

    class Meta:
        ordering = ["id"]

    def __str__(self):
        return f"{self.text} ({'ok' if self.is_correct else 'no'})"


class TajweedQuizAttempt(TimeStamped):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="tajweed_attempts")
    example = models.ForeignKey("TajweedExample", on_delete=models.CASCADE, related_name="attempts")

    correct_rule = models.ForeignKey(
        "TajweedRule",
        null=True, blank=True,
        on_delete=models.SET_NULL,
        related_name="attempts_correct_rule"
    )
    selected_rule = models.ForeignKey(
        "TajweedRule",
        null=True, blank=True,
        on_delete=models.SET_NULL,
        related_name="attempts_selected_rule"
    )

    is_correct = models.BooleanField(default=False)


class UserFavoriteWord(TimeStamped):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="favorite_words")
    word = models.ForeignKey(Word, on_delete=models.CASCADE, related_name="favorited_by")

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["user", "word"], name="uniq_user_favorite_word"),
        ]

    def __str__(self):
        return f"{self.user} ⭐ {self.word.arabic}"




# ----------------------------
# MISSIONS
# ----------------------------
class Mission(TimeStamped):
    MISSION_TYPES = [
        ("review", "Review"),
        ("lesson", "Lesson"),
        ("word", "New Words"),
        ("time", "Study Time"),
    ]
    title = models.CharField(max_length=200)
    description = models.CharField(max_length=255, blank=True)
    points = models.PositiveIntegerField(default=10)
    is_active = models.BooleanField(default=True)
    mission_type = models.CharField(max_length=20, choices=MISSION_TYPES)
    required_count = models.PositiveIntegerField(default=1)  # e.g. 10 reviews
    xp_reward = models.PositiveIntegerField(default=10)

    class Meta:
        ordering = ["id"]

    def __str__(self):
        return f"{self.title} ({self.required_count} {self.mission_type})"


# ----------------------------
# CONVERSATIONAL SCENARIOS
# ----------------------------

class ScenarioCategory(TimeStamped):
    name = models.CharField(max_length=100)
    icon = models.CharField(max_length=50, default="fas fa-comments", help_text="FontAwesome icon class")
    description = models.TextField(blank=True)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        verbose_name_plural = "Scenario Categories"
        ordering = ["order", "id"]

    def __str__(self):
        return self.name


class Scenario(TimeStamped):
    DIFFICULTY_CHOICES = [
        ("beginner", "Beginner"),
        ("intermediate", "Intermediate"),
        ("advanced", "Advanced"),
    ]
    category = models.ForeignKey(ScenarioCategory, on_delete=models.CASCADE, related_name="scenarios")
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    image = models.ImageField(upload_to="scenarios/", blank=True, null=True)
    difficulty = models.CharField(max_length=20, choices=DIFFICULTY_CHOICES, default="beginner")
    xp_reward = models.PositiveIntegerField(default=100)
    is_published = models.BooleanField(default=True)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["order", "id"]

    def __str__(self):
        return self.title


class DialogLine(models.Model):
    scenario = models.ForeignKey(Scenario, on_delete=models.CASCADE, related_name="dialog_lines")
    character_name = models.CharField(max_length=100, help_text="Character name (e.g. Ahmad, Seller)")
    text_arabic = models.TextField()
    text_uz = models.TextField()
    text_ru = models.TextField(blank=True)
    transliteration = models.TextField(blank=True)
    audio = models.FileField(upload_to="audio/dialogs/", blank=True, null=True)
    order = models.PositiveIntegerField(default=0)
    is_user_line = models.BooleanField(default=False, help_text="Should the user answer this?")

    class Meta:
        ordering = ["order"]

    def __str__(self):
        return f"{self.character_name}: {self.text_arabic[:30]}..."


class PhrasebookEntry(TimeStamped):
    category = models.ForeignKey(ScenarioCategory, on_delete=models.SET_NULL, null=True, blank=True, related_name="phrases")
    scenario = models.ForeignKey(Scenario, on_delete=models.SET_NULL, null=True, blank=True, related_name="phrases")
    text_arabic = models.CharField(max_length=255)
    text_uz = models.CharField(max_length=255)
    text_ru = models.CharField(max_length=255, blank=True)
    transliteration = models.CharField(max_length=255, blank=True)
    audio = models.FileField(upload_to="audio/phrases/", blank=True, null=True)

    class Meta:
        verbose_name_plural = "Phrasebook Entries"

    def __str__(self):
        return self.text_arabic


class UserMissionProgress(TimeStamped):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="mission_progress")
    mission = models.ForeignKey(Mission, on_delete=models.CASCADE, related_name="user_progress")
    date = models.DateField(db_index=True, default=timezone.now)
    
    current_progress = models.PositiveIntegerField(default=0)
    is_completed = models.BooleanField(default=False)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["user", "mission", "date"], name="uniq_user_mission_date"),
        ]

    def __str__(self):
        return f"{self.user} - {self.mission} ({self.current_progress}/{self.mission.required_count})"


class UserDailyStat(models.Model):


    """
    Har kunlik statistika: heatmap, streak, weekly chart, daily goals, study time, XP.
    """
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="daily_stats")
    day = models.DateField(db_index=True)

    # Activity
    study_minutes = models.PositiveIntegerField(default=0)
    reviews_done = models.PositiveIntegerField(default=0)
    new_words = models.PositiveIntegerField(default=0)
    lessons_done = models.PositiveIntegerField(default=0)

    # Gamification
    xp_earned = models.PositiveIntegerField(default=0)

    class Meta:
        unique_together = ("user", "day")
        ordering = ("-day",)

    def __str__(self):
        return f"{self.user_id} {self.day}"


class UserGamification(models.Model):
    """
    User umumiy XP/Level.
    """
    LEAGUE_CHOICES = [
        ("BRONZE", "Bronze"),
        ("SILVER", "Silver"),
        ("GOLD", "Gold"),
        ("EMERALD", "Emerald"),
        ("DIAMOND", "Diamond"),
    ]

    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="gamification")
    xp_total = models.PositiveIntegerField(default=0)
    level = models.PositiveIntegerField(default=1)
    
    # Streak Logic
    current_streak = models.PositiveIntegerField(default=0)
    longest_streak = models.PositiveIntegerField(default=0)
    last_study_date = models.DateField(null=True, blank=True)
    streak_freeze_count = models.PositiveIntegerField(default=0)

    # League Logic
    current_league = models.CharField(max_length=20, choices=LEAGUE_CHOICES, default="BRONZE")
    league_xp = models.PositiveIntegerField(default=0, help_text="Weekly XP for league ranking")
    
    # Hearts system
    hearts = models.PositiveIntegerField(default=5)
    last_heart_refill = models.DateTimeField(default=timezone.now)
    badges = models.JSONField(default=list, blank=True)

    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user_id} L{self.level} XP{self.xp_total} {self.current_league}"


class DailyQuest(models.Model):
    """
    Kunlik missiya shablonlari (Admin tomonidan qo'shiladi).
    Masalan: "50 XP yig'ish", "3 ta dars o'tish".
    """
    TYPE_CHOICES = [
        ("XP", "Gain XP"),
        ("LESSON", "Complete Lessons"),
        ("REVIEW", "Review Cards"),
        ("PERFECT", "Perfect Lesson (No mistakes)"),
    ]
    
    title = models.CharField(max_length=200)
    description = models.CharField(max_length=300)
    quest_type = models.CharField(max_length=20, choices=TYPE_CHOICES)
    target_amount = models.PositiveIntegerField(default=1)
    reward_xp = models.PositiveIntegerField(default=20)
    
    def __str__(self):
        return f"{self.title} ({self.target_amount})"


class UserQuestProgress(models.Model):
    """
    Foydalanuvchining bugungi missiyasi holati.
    Har kuni soat 00:00 da regeneratsiya qilinadi.
    """
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="quests")
    quest = models.ForeignKey(DailyQuest, on_delete=models.CASCADE)
    day = models.DateField(default=timezone.now)
    
    progress = models.PositiveIntegerField(default=0)
    is_completed = models.BooleanField(default=False)
    is_claimed = models.BooleanField(default=False)

    class Meta:
        unique_together = ("user", "quest", "day")

    def __str__(self):
        return f"{self.user} - {self.quest}"


        return f"{self.user} - {self.quest.title}"


class UserWeakArea(models.Model):
    """
    Qiyin joylar (weak areas) — siz xohlagan skill/bo'lim bo'yicha foiz.
    pct: 0..100 (qancha past bo'lsa qiyinroq)
    """
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="weak_areas")
    key = models.CharField(max_length=64, db_index=True)  # masalan: "tajweed_idgham"
    title = models.CharField(max_length=128)
    pct = models.PositiveIntegerField(default=0)  # 0..100
    url = models.CharField(max_length=200, blank=True, default="")

    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ("user", "key")
        ordering = ("pct", "-updated_at")

    def __str__(self):
        return f"{self.user_id} {self.key} {self.pct}%"


# ----------------------------
# VIDEO LESSONS
# ----------------------------
class LessonVideo(TimeStamped):
    """
    Video darslik (YouTube/URL).
    Lesson modeliga bog'lanadi. Bitta lesson'da bir nechta video bo'lishi mumkin.
    """
    PROVIDER_CHOICES = (
        ("youtube", "YouTube"),
        ("url", "Direct URL (MP4/Video link)"),
    )

    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE, related_name="videos")
    title = models.CharField(max_length=200)
    provider = models.CharField(max_length=10, choices=PROVIDER_CHOICES, default="youtube")
    
    # YouTube ID yoki to'g'ridan-to'g'ri URL
    video_id = models.CharField(max_length=50, blank=True, help_text="YouTube ID")
    video_url = models.URLField(max_length=500, blank=True, help_text="To'g'ridan-to'g'ri video URL (MP4, yoki boshqa)")
    
    duration = models.PositiveIntegerField(default=0, help_text="Sekundlarda")
    order = models.PositiveIntegerField(default=0)
    is_free = models.BooleanField(default=True)

    class Meta:
        ordering = ["order"]

    def __str__(self):
        return self.title

    @property
    def is_youtube(self):
        if self.provider == "youtube":
            return True
        if self.video_url:
            return "youtube.com" in self.video_url or "youtu.be" in self.video_url
        return False

    @property
    def get_youtube_id(self):
        """
        Extracts YouTube ID from video_id or video_url if provider is youtube.
        """
        if self.video_id and len(self.video_id) == 11:
            return self.video_id
        
        target = self.video_url or self.video_id or ""
        import re
        # Regex for various Youtube URL formats
        regex = r'(?:youtube\.com\/(?:[^\/]+\/.+\/|(?:v|e(?:mbed)?)\/|.*[?&]v=)|youtu\.be\/)([^"&?\/\s]{11})'
        match = re.search(regex, target)
        if match:
            return match.group(1)
        return self.video_id

    @property
    def get_url(self):
        if self.provider == "youtube":
            y_id = self.get_youtube_id
            return f"https://www.youtube.com/embed/{y_id}"
        if self.video_url:
            return self.video_url
        return ""


class UserVideoProgress(TimeStamped):
    """
    User videoni qancha ko'rdi.
    """
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="video_progress")
    video = models.ForeignKey(LessonVideo, on_delete=models.CASCADE, related_name="progress")
    
    progress_seconds = models.PositiveIntegerField(default=0)
    is_watched = models.BooleanField(default=False)
    
    class Meta:
        unique_together = ("user", "video")

    def __str__(self):
        return f"{self.user} - {self.video} ({self.progress_seconds}s)"


# ----------------------------
# PROFILE
# ----------------------------
class Profile(TimeStamped):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="profile")
    avatar = models.ImageField(upload_to="avatars/", blank=True, null=True)
    bio = models.TextField(max_length=500, blank=True)
    current_course = models.ForeignKey("Course", on_delete=models.SET_NULL, null=True, blank=True, related_name="students")
    has_taken_placement_test = models.BooleanField(default=False, help_text="Whether user has completed placement test")

    def __str__(self):
        return f"{self.user.username}'s profile"

class UserReminder(TimeStamped):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="reminder_settings")
    reminder_time = models.TimeField(null=True, blank=True, help_text="Daily reminder time")
    is_enabled = models.BooleanField(default=False)
    notes = models.TextField(blank=True, help_text="User notes / eslatmalar")
    push_subscription = models.JSONField(null=True, blank=True, help_text="Browser push subscription data")

    def __str__(self):
        return f"Reminder for {self.user.username} at {self.reminder_time}"

# Signals to auto-create/save Profile and Reminder
from django.db.models.signals import post_save
from django.dispatch import receiver

@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_user_related_objects(sender, instance, created, **kwargs):
    if created:
        Profile.objects.get_or_create(user=instance)
        UserReminder.objects.get_or_create(user=instance)

@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def save_user_related_objects(sender, instance, **kwargs):
    if hasattr(instance, 'profile'):
        instance.profile.save()
    if hasattr(instance, 'reminder_settings'):
        instance.reminder_settings.save()

# ----------------------------
# FEEDBACK
# ----------------------------
class UserFeedback(TimeStamped):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    type = models.CharField(max_length=20, choices=[
        ('suggestion', 'Taklif'),
        ('problem', 'Muammo'),
        ('other', 'Boshqa')
    ], default='suggestion')
    message = models.TextField()
    is_resolved = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.user.username} - {self.type}"


# ----------------------------
# TAVSIF - DESCRIPTIVE DICTIONARY (MODULE 1)
# ----------------------------
class TavsifNoun(TimeStamped):
    """Ot (Noun) for Tavsif - with all grammatical forms"""
    arabic = models.CharField(max_length=100, unique=True)
    arabic_definite = models.CharField(max_length=100, blank=True)  # ال + noun
    transliteration = models.CharField(max_length=150, blank=True)
    translation_uz = models.CharField(max_length=200)
    
    GENDER_CHOICES = [("M", "Muzakkar (Masculine)"), ("F", "Muannas (Feminine)")]
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES, default="M")
    
    NUMBER_CHOICES = [("S", "Mufrad (Singular)"), ("D", "Mutsanna (Dual)"), ("P", "Jam' (Plural)")]
    number = models.CharField(max_length=1, choices=NUMBER_CHOICES, default="S")
    
    # Dual and Plural forms
    dual_form = models.CharField(max_length=100, blank=True)
    plural_form = models.CharField(max_length=100, blank=True)
    plural_type = models.CharField(max_length=20, blank=True, help_text="jam' salim/jam' taksir")
    
    audio = models.FileField(upload_to="audio/tavsif/nouns/", blank=True, null=True)
    
    class Meta:
        ordering = ["arabic"]
        verbose_name = "Tavsif - Ot (Noun)"
        verbose_name_plural = "Tavsif - Otlar"
    
    def __str__(self):
        return f"{self.arabic} ({self.translation_uz})"


class TavsifAdjective(TimeStamped):
    """Sifat (Adjective) for Tavsif - with all grammatical forms"""
    arabic_masc = models.CharField(max_length=100, help_text="Muzakkar shakl")
    arabic_fem = models.CharField(max_length=100, blank=True, help_text="Muannas shakl")
    transliteration = models.CharField(max_length=150, blank=True)
    translation_uz = models.CharField(max_length=200)
    
    # Plural forms
    masc_plural = models.CharField(max_length=100, blank=True)
    fem_plural = models.CharField(max_length=100, blank=True)
    
    # Dual forms
    masc_dual = models.CharField(max_length=100, blank=True)
    fem_dual = models.CharField(max_length=100, blank=True)
    
    audio = models.FileField(upload_to="audio/tavsif/adjectives/", blank=True, null=True)
    
    class Meta:
        ordering = ["arabic_masc"]
        verbose_name = "Tavsif - Sifat (Adjective)"
        verbose_name_plural = "Tavsif - Sifatlar"
    
    def __str__(self):
        return f"{self.arabic_masc} / {self.arabic_fem}"
    
    def get_form(self, gender='M', number='S', definite=False):
        """Get correct adjective form based on gender, number, definiteness"""
        if number == 'S':
            base = self.arabic_masc if gender == 'M' else self.arabic_fem
        elif number == 'D':
            base = self.masc_dual if gender == 'M' else self.fem_dual
        else:  # Plural
            base = self.masc_plural if gender == 'M' else self.fem_plural
        
        if definite and base:
            return f"ال{base}"
        return base or self.arabic_masc


class TavsifPhrase(TimeStamped):
    """Complete Tavsif phrase (Noun + Adjective) with auto-correction"""
    noun = models.ForeignKey(TavsifNoun, on_delete=models.CASCADE, related_name="phrases")
    adjective = models.ForeignKey(TavsifAdjective, on_delete=models.CASCADE, related_name="phrases")
    
    # Pre-computed correct forms
    correct_phrase = models.CharField(max_length=250, blank=True, help_text="Auto-generated correct form")
    correct_phrase_definite = models.CharField(max_length=250, blank=True)
    
    example_sentence = models.TextField(blank=True, help_text="Example sentence in Arabic")
    example_translation = models.CharField(max_length=500, blank=True)
    
    audio = models.FileField(upload_to="audio/tavsif/phrases/", blank=True, null=True)
    
    class Meta:
        ordering = ["noun__arabic"]
        unique_together = ("noun", "adjective")
        verbose_name = "Tavsif - Ibora"
        verbose_name_plural = "Tavsif - Iboralar"
    
    def __str__(self):
        return self.correct_phrase or f"{self.noun.arabic} {self.adjective.arabic_masc}"
    
    def save(self, *args, **kwargs):
        # Auto-generate correct phrase based on agreement rules
        self.correct_phrase = self.generate_correct_phrase(definite=False)
        self.correct_phrase_definite = self.generate_correct_phrase(definite=True)
        super().save(*args, **kwargs)
    
    def generate_correct_phrase(self, definite=False):
        """Generate grammatically correct phrase with agreement"""
        noun = self.noun
        adj = self.adjective
        
        # Get adjective form matching noun's gender and number
        adj_form = adj.get_form(gender=noun.gender, number=noun.number, definite=definite)
        
        if definite:
            noun_form = noun.arabic_definite or f"ال{noun.arabic}"
        else:
            noun_form = noun.arabic
        
        return f"{noun_form} {adj_form}"


# ----------------------------
# SARF - ARABIC MORPHOLOGY (MODULE 2)
# ----------------------------
class ArabicRoot(TimeStamped):
    """Arabic trilateral/quadrilateral root"""
    letters = models.CharField(max_length=10, unique=True, help_text="Root letters, e.g. ك ت ب")
    meaning = models.CharField(max_length=200, help_text="Core meaning of root")
    translation_uz = models.CharField(max_length=200)
    
    PATTERN_CHOICES = [
        ("3", "Thulathi (3 letters)"),
        ("4", "Ruba'i (4 letters)"),
    ]
    pattern = models.CharField(max_length=1, choices=PATTERN_CHOICES, default="3")
    
    class Meta:
        ordering = ["letters"]
        verbose_name = "Sarf - Ildiz (Root)"
        verbose_name_plural = "Sarf - Ildizlar"
    
    def __str__(self):
        return f"{self.letters} ({self.meaning})"


class SarfDerivation(TimeStamped):
    """Derived word forms from a root"""
    root = models.ForeignKey(ArabicRoot, on_delete=models.CASCADE, related_name="derivations")
    
    FORM_CHOICES = [
        ("past", "Fi'l Madi (O'tgan zamon)"),
        ("present", "Fi'l Mudori (Hozirgi zamon)"),
        ("masdar", "Masdar (Ot-fe'l)"),
        ("active_part", "Ism Fa'il (Faol sifatdosh)"),
        ("passive_part", "Ism Maf'ul (Majhul sifatdosh)"),
        ("place", "Ism Makan (Joy oti)"),
        ("tool", "Ism Ala (Asbob oti)"),
        ("intensive", "Mubalaghah (Kuchaytirilgan shakl)"),
    ]
    form_type = models.CharField(max_length=20, choices=FORM_CHOICES)
    
    arabic = models.CharField(max_length=100)
    wazn = models.CharField(max_length=50, blank=True, help_text="Pattern/Wazn, e.g. فَاعِل")
    transliteration = models.CharField(max_length=150, blank=True)
    translation_uz = models.CharField(max_length=200)
    explanation = models.TextField(blank=True, help_text="How this form is derived")
    
    audio = models.FileField(upload_to="audio/sarf/", blank=True, null=True)
    
    class Meta:
        ordering = ["root", "form_type"]
        unique_together = ("root", "form_type", "arabic")
        verbose_name = "Sarf - Hosila"
        verbose_name_plural = "Sarf - Hosilalar"
    
    def __str__(self):
        return f"{self.arabic} ({self.get_form_type_display()})"


# ----------------------------
# NAHV - ARABIC GRAMMAR (MODULE 2)
# ----------------------------
class NahvSentence(TimeStamped):
    """Arabic sentence for grammar analysis"""
    arabic_text = models.TextField()
    translation_uz = models.TextField()
    transliteration = models.TextField(blank=True)
    
    SENTENCE_TYPES = [
        ("nominal", "Jumla Ismiya (Ot gapi)"),
        ("verbal", "Jumla Fi'liya (Fe'l gapi)"),
    ]
    sentence_type = models.CharField(max_length=20, choices=SENTENCE_TYPES)
    
    level = models.CharField(max_length=10, choices=[("A0","A0"),("A1","A1"),("A2","A2"),("B1","B1")], default="A0")
    
    audio = models.FileField(upload_to="audio/nahv/", blank=True, null=True)
    
    class Meta:
        ordering = ["level", "id"]
        verbose_name = "Nahv - Gap"
        verbose_name_plural = "Nahv - Gaplar"
    
    def __str__(self):
        return self.arabic_text[:50]


class NahvWordAnalysis(TimeStamped):
    """I'rab analysis of a word in a sentence"""
    sentence = models.ForeignKey(NahvSentence, on_delete=models.CASCADE, related_name="word_analyses")
    
    word = models.CharField(max_length=100)
    position = models.PositiveIntegerField(help_text="Word position in sentence")
    
    ROLE_CHOICES = [
        ("mubtada", "Mubtada (Ega)"),
        ("khabar", "Xabar (Kesim)"),
        ("fail", "Fa'il (Bajaruvchi)"),
        ("mafool_bihi", "Maf'ul Bihi (To'ldiruvchi)"),
        ("fiil", "Fi'l (Fe'l)"),
        ("jar_majroor", "Jar va Majrur"),
        ("mudaf", "Mudof"),
        ("mudaf_ilayh", "Mudof ilayh"),
        ("sifat", "Sifat"),
        ("mansub", "Mansub"),
        ("majroor", "Majrur"),
        ("marfoo", "Marfu'"),
        ("harf", "Harf"),
    ]
    grammatical_role = models.CharField(max_length=30, choices=ROLE_CHOICES)
    
    IRAB_CHOICES = [
        ("marfoo", "Marfu' (و / ون / ان)"),
        ("mansub", "Mansub (ا / ين / ين)"),
        ("majroor", "Majrur (ي / ين / ين)"),
        ("mabni", "Mabni (O'zgarmaydi)"),
    ]
    irab = models.CharField(max_length=20, choices=IRAB_CHOICES, blank=True)
    irab_sign = models.CharField(max_length=50, blank=True, help_text="e.g. Damma, Fatha, Kasra")
    
    explanation_uz = models.TextField(help_text="I'rab tushuntirish o'zbekcha")
    
    class Meta:
        ordering = ["sentence", "position"]
        verbose_name = "Nahv - So'z tahlili"
        verbose_name_plural = "Nahv - So'z tahlillari"
    
    def __str__(self):
        return f"{self.word} ({self.get_grammatical_role_display()})"


# ----------------------------
# VERB CONJUGATION (MODULE 5)
# ----------------------------
class ArabicVerb(TimeStamped):
    """Arabic verb with all conjugation forms"""
    root = models.ForeignKey(ArabicRoot, on_delete=models.SET_NULL, null=True, blank=True, related_name="verbs")
    
    # Past tense base form (3rd person masculine singular)
    past_base = models.CharField(max_length=50, help_text="Fi'l Madi (Huwa)")
    present_base = models.CharField(max_length=50, help_text="Fi'l Mudori (Huwa)")
    command_base = models.CharField(max_length=50, blank=True, help_text="Fi'l Amr (Anta)")
    masdar = models.CharField(max_length=50, blank=True)
    
    transliteration = models.CharField(max_length=100, blank=True)
    translation_uz = models.CharField(max_length=200)
    
    VERB_FORM_CHOICES = [
        ("1", "Form I (Fa'ala)"),
        ("2", "Form II (Fa''ala)"),
        ("3", "Form III (Faa'ala)"),
        ("4", "Form IV (Af'ala)"),
        ("5", "Form V (Tafa''ala)"),
        ("6", "Form VI (Tafaa'ala)"),
        ("7", "Form VII (Infa'ala)"),
        ("8", "Form VIII (Ifta'ala)"),
        ("9", "Form IX (If'alla)"),
        ("10", "Form X (Istaf'ala)"),
    ]
    verb_form = models.CharField(max_length=2, choices=VERB_FORM_CHOICES, default="1")
    
    audio = models.FileField(upload_to="audio/verbs/", blank=True, null=True)
    
    class Meta:
        ordering = ["past_base"]
        verbose_name = "Fe'l (Verb)"
        verbose_name_plural = "Fe'llar (Verbs)"
    
    def __str__(self):
        return f"{self.past_base} - {self.translation_uz}"


class VerbConjugation(TimeStamped):
    """Individual conjugation of a verb"""
    verb = models.ForeignKey(ArabicVerb, on_delete=models.CASCADE, related_name="conjugations")
    
    TENSE_CHOICES = [
        ("past", "Moʻziy (O'tgan zamon)"),
        ("present", "Mudori (Hozirgi/Kelasi)"),
        ("command", "Amr (Buyruq)"),
    ]
    tense = models.CharField(max_length=10, choices=TENSE_CHOICES)
    
    PERSON_CHOICES = [
        ("1s", "Ana (Men)"),
        ("1p", "Nahnu (Biz)"),
        ("2ms", "Anta (Sen - erkak)"),
        ("2fs", "Anti (Sen - ayol)"),
        ("2mp", "Antum (Sizlar - erkak)"),
        ("2fp", "Antunna (Sizlar - ayol)"),
        ("3ms", "Huwa (U - erkak)"),
        ("3fs", "Hiya (U - ayol)"),
        ("3mp", "Hum (Ular - erkak)"),
        ("3fp", "Hunna (Ular - ayol)"),
        ("2md", "Antuma (Ikkalangiz)"),
        ("3md", "Huma (Ikkalasi - erkak)"),
        ("3fd", "Huma (Ikkalasi - ayol)"),
    ]
    person = models.CharField(max_length=5, choices=PERSON_CHOICES)
    
    conjugated_form = models.CharField(max_length=100)
    transliteration = models.CharField(max_length=150, blank=True)
    
    audio = models.FileField(upload_to="audio/conjugations/", blank=True, null=True)
    
    class Meta:
        ordering = ["verb", "tense", "person"]
        unique_together = ("verb", "tense", "person")
        verbose_name = "Fe'l tuslanishi"
        verbose_name_plural = "Fe'l tuslanishlari"
    
    def __str__(self):
        return f"{self.conjugated_form} ({self.get_person_display()} - {self.get_tense_display()})"


# ----------------------------
# SENTENCE BUILDING (MODULE 4)
# ----------------------------
class SentenceExercise(TimeStamped):
    """Sentence building exercise"""
    EXERCISE_TYPES = [
        ("word_order", "So'z tartibi"),
        ("translation", "Tarjima (UZ → AR)"),
        ("fill_blank", "Bo'sh joyni to'ldiring"),
        ("correction", "Xatoni tuzating"),
    ]
    exercise_type = models.CharField(max_length=20, choices=EXERCISE_TYPES)
    
    arabic_sentence = models.TextField(help_text="To'g'ri javob")
    uzbek_sentence = models.TextField()
    
    # For word order exercises - shuffled words
    word_options = models.JSONField(default=list, help_text="Aralashtirilgan so'zlar ro'yxati")
    
    # For fill in blank
    sentence_with_blank = models.TextField(blank=True, help_text="Gap _____ bilan")
    correct_word = models.CharField(max_length=100, blank=True)
    
    level = models.CharField(max_length=10, choices=[("A0","A0"),("A1","A1"),("A2","A2"),("B1","B1")], default="A0")
    
    hint = models.CharField(max_length=300, blank=True, help_text="Yordam")
    explanation = models.TextField(blank=True, help_text="Grammatika tushuntirishi")
    
    audio = models.FileField(upload_to="audio/sentences/", blank=True, null=True)
    
    class Meta:
        ordering = ["level", "exercise_type"]
        verbose_name = "Gap mashqi"
        verbose_name_plural = "Gap mashqlari"
    
    def __str__(self):
        return self.arabic_sentence[:50]


# ----------------------------
# SPEAKING LESSONS (MODULE 6)
# ----------------------------
class SpeakingCategory(TimeStamped):
    """Category for speaking lessons"""
    name = models.CharField(max_length=100)
    name_uz = models.CharField(max_length=100)
    icon = models.CharField(max_length=50, default="fas fa-microphone")
    description = models.TextField(blank=True)
    order = models.PositiveIntegerField(default=0)
    
    class Meta:
        ordering = ["order"]
        verbose_name = "Gapirish kategoriyasi"
        verbose_name_plural = "Gapirish kategoriyalari"
    
    def __str__(self):
        return self.name_uz


class SpeakingLesson(TimeStamped):
    """100 speaking lessons with dialogues"""
    category = models.ForeignKey(SpeakingCategory, on_delete=models.CASCADE, related_name="lessons")
    
    lesson_number = models.PositiveIntegerField()
    title = models.CharField(max_length=200)
    title_uz = models.CharField(max_length=200)
    
    # Main dialogue
    dialogue_arabic = models.TextField(help_text="Full dialogue in Arabic")
    dialogue_uz = models.TextField(help_text="Uzbek translation")
    dialogue_transliteration = models.TextField(blank=True)
    
    # Key phrases
    key_phrases = models.JSONField(default=list, help_text="Key phrases to learn [{'ar': '', 'uz': '', 'audio': ''}]")
    
    # Q&A tasks
    qa_tasks = models.JSONField(default=list, help_text="Speaking tasks [{'question_ar': '', 'question_uz': '', 'sample_answer': ''}]")
    
    audio_dialogue = models.FileField(upload_to="audio/speaking/dialogues/", blank=True, null=True)
    audio_slow = models.FileField(upload_to="audio/speaking/slow/", blank=True, null=True, help_text="Slow version")
    
    level = models.CharField(max_length=20, choices=[("beginner","Boshlang'ich"),("intermediate","O'rta"),("advanced","Yuqori")], default="beginner")
    xp_reward = models.PositiveIntegerField(default=50)
    estimated_minutes = models.PositiveIntegerField(default=10)
    
    class Meta:
        ordering = ["category", "lesson_number"]
        unique_together = ("category", "lesson_number")
        verbose_name = "Gapirish darsi"
        verbose_name_plural = "Gapirish darslari"
    
    def __str__(self):
        return f"{self.lesson_number}. {self.title_uz}"


class SpeakingPractice(TimeStamped):
    """User's speaking practice session"""
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="speaking_practices")
    lesson = models.ForeignKey(SpeakingLesson, on_delete=models.CASCADE, related_name="practices")
    
    is_completed = models.BooleanField(default=False)
    phrases_practiced = models.PositiveIntegerField(default=0)
    qa_completed = models.PositiveIntegerField(default=0)
    
    # Optional: user's recorded audio
    user_recording = models.FileField(upload_to="audio/user_recordings/", blank=True, null=True)
    
    class Meta:
        unique_together = ("user", "lesson")
        verbose_name = "Gapirish amaliyoti"
        verbose_name_plural = "Gapirish amaliyotlari"
    
    def __str__(self):
        return f"{self.user.username} - {self.lesson.title_uz}"
