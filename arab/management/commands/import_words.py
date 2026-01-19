import csv
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from arab.models import Word, VocabularyCategory, Lesson


class Command(BaseCommand):
    help = "CSV fayldan Word'larni import qiladi (1000+ so'z uchun)."

    def add_arguments(self, parser):
        parser.add_argument("csv_path", type=str, help="CSV fayl yo'li")
        parser.add_argument("--dry-run", action="store_true", help="DBga yozmaydi, faqat tekshiradi")

    @transaction.atomic
    def handle(self, *args, **options):
        csv_path = options["csv_path"]
        dry = options["dry_run"]

        created, updated, skipped = 0, 0, 0

        try:
            f = open(csv_path, "r", encoding="utf-8-sig", newline="")
        except FileNotFoundError:
            raise CommandError(f"CSV topilmadi: {csv_path}")

        with f:
            reader = csv.DictReader(f)
            required = {"arabic", "transliteration", "uz", "ru", "category", "lesson_id"}
            missing_cols = required - set(reader.fieldnames or [])
            if missing_cols:
                raise CommandError(f"CSV ustunlari yetishmayapti: {', '.join(sorted(missing_cols))}")

            for i, row in enumerate(reader, start=2):
                arabic = (row.get("arabic") or "").strip()
                if not arabic:
                    skipped += 1
                    self.stdout.write(self.style.WARNING(f"{i}-qatorda arabic bo'sh, skip"))
                    continue

                translit = (row.get("transliteration") or "").strip()
                uz = (row.get("uz") or "").strip()
                ru = (row.get("ru") or "").strip()
                cat_name = (row.get("category") or "").strip() or "General"

                lesson_id_raw = (row.get("lesson_id") or "").strip()
                lesson = None
                if lesson_id_raw:
                    try:
                        lesson = Lesson.objects.get(id=int(lesson_id_raw))
                    except (ValueError, Lesson.DoesNotExist):
                        self.stdout.write(self.style.WARNING(f"{i}-qatorda lesson_id noto'g'ri: {lesson_id_raw}, lesson=None"))

                category, _ = VocabularyCategory.objects.get_or_create(name=cat_name, defaults={"description": ""})

                # Upsert: arabic + lesson bo'yicha (MVP)
                obj, created_flag = Word.objects.update_or_create(
                    arabic=arabic,
                    lesson=lesson,
                    defaults={
                        "transliteration": translit,
                        "translation_uz": uz,
                        "translation_ru": ru,
                        "category": category,
                    }
                )

                if created_flag:
                    created += 1
                else:
                    updated += 1

        if dry:
            transaction.set_rollback(True)
            self.stdout.write(self.style.WARNING("DRY-RUN: DBga yozilmadi (rollback)"))

        self.stdout.write(self.style.SUCCESS(
            f"Done ✅ created={created} updated={updated} skipped={skipped}"
        ))
