from django.core.management.base import BaseCommand
from django.db import transaction
from django.contrib.auth import get_user_model

from arab.models import TajweedTag, TajweedMark, TajweedRule


TAGS = [
    ("Mad", "amber"),
    ("Ghunnah", "emerald"),
    ("Ikhfa", "sky"),
    ("Idg‘om", "violet"),
    ("Qalqala", "rose"),
]


class Command(BaseCommand):
    help = "TajweedTag larni qo‘shadi va sample highlight (mark) yaratadi."

    def add_arguments(self, parser):
        parser.add_argument(
            "--username",
            type=str,
            default="admin",
            help="Marklarni qaysi userga bog‘lash (default: admin)",
        )

    @transaction.atomic
    def handle(self, *args, **opts):
        username = opts["username"]
        User = get_user_model()

        user, _ = User.objects.get_or_create(
            username=username,
            defaults={"is_staff": True, "is_superuser": True},
        )

        tag_objs = {}
        for name, color in TAGS:
            tag, _ = TajweedTag.objects.update_or_create(name=name, defaults={"color": color})
            tag_objs[name] = tag

        # Sample highlight: mad-qoidalari -> "قَالَ" ichidagi "ا" ni bo'yash
        rule = TajweedRule.objects.filter(slug="mad-qoidalari").first()
        if not rule:
            self.stdout.write(self.style.WARNING("Rule topilmadi: mad-qoidalari"))
            return

        ex = rule.examples.filter(arabic_text="قَالَ").first()
        if not ex:
            self.stdout.write(self.style.WARNING('Example topilmadi: "قَالَ" (avval seed_tajweed_examples ishlasin)'))
            return

        start = ex.arabic_text.find("ا")
        if start == -1:
            self.stdout.write(self.style.WARNING('Index topilmadi: "ا"'))
            return

        end = start + 1

        TajweedMark.objects.update_or_create(
            user=user,          # ✅ MUHIM
            example=ex,
            rule=rule,
            start=start,
            end=end,
            defaults={
                "tag": tag_objs["Mad"],
                "note": "Mad harfi (namuna highlight)",
            },
        )

        self.stdout.write(self.style.SUCCESS("✅ Done. Tags + sample highlight created."))
