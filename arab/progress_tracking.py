from __future__ import annotations

from dataclasses import dataclass
from datetime import timedelta
from django.db import transaction
from django.utils import timezone

from .models import UserDailyStat, UserGamification


# XP qoidalari (xohlasangiz o'zgartirasiz)
XP_PER_REVIEW = 1
XP_PER_NEW_WORD = 2
XP_PER_LESSON = 10
XP_PER_MINUTE = 0  # agar vaqtga ham XP bermoqchi bo'lsangiz (masalan 1) qiling


def xp_for_next_level(level: int) -> int:
    """
    Next level uchun kerak bo'ladigan XP.
    Oddiy formula: 100 * level
    """
    return 100 * max(1, level)


@transaction.atomic
def _get_or_create_today(user):
    today = timezone.localdate()
    stat, _ = UserDailyStat.objects.get_or_create(user=user, day=today)
    g, _ = UserGamification.objects.get_or_create(user=user)
    return stat, g


def _apply_leveling(g: UserGamification):
    """
    XP oshganidan keyin level up bo'lsa update qiladi.
    """
    while True:
        need = xp_for_next_level(g.level)
        # Level-up sharti: xp_total >= need * level? (bizda need = 100*level)
        # Buni "threshold" sifatida ishlatamiz:
        if g.xp_total >= need:
            g.level += 1
            # xp_totalni kamaytirish emas, umumiy XP qolsin.
            # Agar "level XP" alohida bo'lsin desangiz, shu yerda subtract qilasiz.
            continue
        break


@transaction.atomic
def track_review(user, count: int = 1):
    stat, g = _get_or_create_today(user)
    stat.reviews_done += max(0, int(count))
    gained = max(0, int(count)) * XP_PER_REVIEW
    stat.xp_earned += gained
    g.xp_total += gained
    _apply_leveling(g)
    stat.save(update_fields=["reviews_done", "xp_earned"])
    g.save(update_fields=["xp_total", "level", "updated_at"])


@transaction.atomic
def track_new_word(user, count: int = 1):
    stat, g = _get_or_create_today(user)
    stat.new_words += max(0, int(count))
    gained = max(0, int(count)) * XP_PER_NEW_WORD
    stat.xp_earned += gained
    g.xp_total += gained
    _apply_leveling(g)
    stat.save(update_fields=["new_words", "xp_earned"])
    g.save(update_fields=["xp_total", "level", "updated_at"])


@transaction.atomic
def track_lesson_done(user, count: int = 1):
    stat, g = _get_or_create_today(user)
    stat.lessons_done += max(0, int(count))
    gained = max(0, int(count)) * XP_PER_LESSON
    stat.xp_earned += gained
    g.xp_total += gained
    _apply_leveling(g)
    stat.save(update_fields=["lessons_done", "xp_earned"])
    g.save(update_fields=["xp_total", "level", "updated_at"])


@transaction.atomic
def track_study_minutes(user, minutes: int = 1):
    stat, g = _get_or_create_today(user)
    mins = max(0, int(minutes))
    stat.study_minutes += mins
    gained = mins * XP_PER_MINUTE
    stat.xp_earned += gained
    g.xp_total += gained
    _apply_leveling(g)
    stat.save(update_fields=["study_minutes", "xp_earned"])
    g.save(update_fields=["xp_total", "level", "updated_at"])
