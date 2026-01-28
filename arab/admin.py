from django.contrib import admin
from .models import (
    Course, Unit, Lesson,
    Letter, Diacritic,
    Word, WordExample, VocabularyCategory,
    Exercise, Question, Choice,
    UserLessonProgress, UserWordProgress, UserQuizAttempt,
    LessonVideo, UserVideoProgress, Profile,
    ScenarioCategory, Scenario, DialogLine, PhrasebookEntry,
    Mission, UserMissionProgress, UserGamification, UserDailyStat
)

@admin.register(ScenarioCategory)
class ScenarioCategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "order")

class DialogLineInline(admin.TabularInline):
    model = DialogLine
    extra = 3

@admin.register(Scenario)
class ScenarioAdmin(admin.ModelAdmin):
    list_display = ("title", "category", "difficulty", "is_published")
    list_filter = ("category", "difficulty", "is_published")
    inlines = [DialogLineInline]

@admin.register(PhrasebookEntry)
class PhrasebookEntryAdmin(admin.ModelAdmin):
    list_display = ("text_arabic", "text_uz", "category", "scenario")
    search_fields = ("text_arabic", "text_uz", "text_ru")

from .models import TajweedRule, TajweedExample, TajweedTag, TajweedMark, TajweedQuiz, TajweedQuizOption, TajweedQuizAttempt , LetterExample

class TajweedQuizOptionInline(admin.TabularInline):
    model = TajweedQuizOption
    extra = 0

class TajweedMarkInline(admin.TabularInline):
    model = TajweedMark
    extra = 0

@admin.register(TajweedExample)
class TajweedExampleAdmin(admin.ModelAdmin):
    list_display = ("id", "rule", "arabic_text_short")
    search_fields = ("arabic_text", "translation_uz", "rule__title")
    inlines = [TajweedMarkInline]

    def arabic_text_short(self, obj):
        t = obj.arabic_text or ""
        return (t[:60] + "...") if len(t) > 60 else t


@admin.register(TajweedRule)
class TajweedRuleAdmin(admin.ModelAdmin):
    list_display = ("title", "level", "is_published")
    list_filter = ("level", "is_published")
    search_fields = ("title", "short_desc", "explanation")
    prepopulated_fields = {"slug": ("title",)}


@admin.register(TajweedTag)
class TajweedTagAdmin(admin.ModelAdmin):
    list_display = ("name", "color")
    search_fields = ("name",)


@admin.register(TajweedMark)
class TajweedMarkAdmin(admin.ModelAdmin):
    list_display = ("example", "rule", "tag", "start", "end")
    list_filter = ("rule", "tag")


# ----------------- Inline'lar -----------------
class UnitInline(admin.TabularInline):
    model = Unit
    extra = 0
    
class LessonInline(admin.TabularInline):
    model = Lesson
    extra = 0

class WordExampleInline(admin.TabularInline):
    model = WordExample
    extra = 0

class ChoiceInline(admin.TabularInline):
    model = Choice
    extra = 0

class QuestionInline(admin.TabularInline):
    model = Question
    extra = 0


# ----------------- Course / Unit / Lesson -----------------
@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ("title", "level", "is_published", "created_at", "updated_at")
    list_filter = ("level", "is_published")
    search_fields = ("title", "description")
    ordering = ("level", "title")
    inlines = (UnitInline,)


@admin.register(Unit)
class UnitAdmin(admin.ModelAdmin):
    list_display = ("title", "course", "order", "created_at")
    list_filter = ("course",)
    search_fields = ("title", "course__title")
    ordering = ("course", "order")
    inlines = (LessonInline,)


@admin.register(Lesson)
class LessonAdmin(admin.ModelAdmin):
    list_display = ("title", "unit", "order", "estimated_minutes", "created_at")
    list_filter = ("unit__course", "unit")
    search_fields = ("title", "theory", "unit__title", "unit__course__title")
    ordering = ("unit", "order")


@admin.register(LessonVideo)
class LessonVideoAdmin(admin.ModelAdmin):
    list_display = ("title", "lesson", "provider", "duration", "is_free", "created_at")
    list_filter = ("provider", "is_free", "lesson__unit__course")
    search_fields = ("title", "video_id", "lesson__title")
    ordering = ("lesson", "order")
    
    fieldsets = (
        ("Asosiy ma'lumotlar", {
            "fields": ("lesson", "title", "order", "is_free")
        }),
        ("Video manbasi", {
            "fields": ("provider", "video_id", "video_url"),
            "description": "YouTube uchun: video ID ni kiriting (masalan: dQw4w9WgXcQ). Direct URL uchun: to'liq video linkni kiriting."
        }),
        ("Qo'shimcha", {
            "fields": ("duration",),
            "description": "Video davomiyligi sekundlarda"
        }),
    )


# ----------------- Letter / Diacritic -----------------
@admin.register(Letter)
class LetterAdmin(admin.ModelAdmin):
    list_display = ("order", "name", "arabic", "joins_to_next")
    list_filter = ("joins_to_next",)
    search_fields = ("name", "arabic")
    ordering = ("order",)
    list_editable = ("joins_to_next",)


@admin.register(Diacritic)
class DiacriticAdmin(admin.ModelAdmin):
    list_display = ("key", "symbol", "description", "created_at")
    list_filter = ("key",)
    search_fields = ("key", "symbol", "description")
    ordering = ("key",)


# ----------------- Word -----------------
@admin.register(VocabularyCategory)
class VocabularyCategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "description")
    search_fields = ("name",)

@admin.register(Word)
class WordAdmin(admin.ModelAdmin):
    list_display = ("arabic", "translation_uz") # DEBUG: removed lesson, category, translation_ru, created_at
    list_filter = ("category", "lesson__unit__course", "lesson")
    search_fields = ("arabic", "transliteration", "translation_uz", "translation_ru")
    ordering = ("arabic",)
    filter_horizontal = ("diacritics",)
    inlines = (WordExampleInline,)


@admin.register(WordExample)
class WordExampleAdmin(admin.ModelAdmin):
    list_display = ("arabic_text", "word", "translation_uz", "created_at")
    search_fields = ("arabic_text", "word__arabic", "translation_uz")
    list_filter = ("word",)
    ordering = ("-created_at",)


# ----------------- Exercise / Quiz -----------------
@admin.register(Exercise)
class ExerciseAdmin(admin.ModelAdmin):
    list_display = ("title", "lesson", "type", "created_at")
    list_filter = ("type", "lesson")
    search_fields = ("title", "instruction")
    inlines = [QuestionInline]

@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    inlines = [ChoiceInline]


@admin.register(Choice)
class ChoiceAdmin(admin.ModelAdmin):
    list_display = ("text", "question", "is_correct")
    list_filter = ("is_correct",)
    search_fields = ("text", "question__prompt")
    ordering = ("question", "-is_correct")


# ----------------- Progress & Stats -----------------
@admin.register(UserLessonProgress)
class UserLessonProgressAdmin(admin.ModelAdmin):
    list_display = ("user", "lesson", "percent", "is_completed", "updated_at")
    list_filter = ("is_completed", "lesson__unit__course")
    search_fields = ("user__username", "user__email", "lesson__title")
    ordering = ("-updated_at",)


@admin.register(UserWordProgress)
class UserWordProgressAdmin(admin.ModelAdmin):
    list_display = ("user", "word", "strength", "last_seen", "updated_at")
    list_filter = ("word__lesson__unit__course",)
    search_fields = ("user__username", "user__email", "word__arabic")
    ordering = ("-updated_at",)


@admin.register(UserQuizAttempt)
class UserQuizAttemptAdmin(admin.ModelAdmin):
    list_display = ("user", "exercise", "score", "total", "created_at")
    list_filter = ("exercise__type", "exercise__lesson__unit__course")
    search_fields = ("user__username", "user__email", "exercise__title")
    ordering = ("-created_at",)

@admin.register(LetterExample)
class UserLetterExampleAdmin(admin.ModelAdmin):
    pass

@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "avatar", "created_at")
    search_fields = ("user__username", "user__email")