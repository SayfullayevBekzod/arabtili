import random
from django.core.management.base import BaseCommand
from django.db import transaction

from arab.models import TajweedRule, TajweedQuiz, TajweedQuizOption


class Command(BaseCommand):
    help = "TajweedRule lar asosida quiz yaratadi (har qoidaga 1 savol + 4 variant)."

    def add_arguments(self, parser):
        parser.add_argument("--clear", action="store_true", help="Oldingi quizlarni o‘chirib qayta yaratadi")
        parser.add_argument("--per-rule", type=int, default=1, help="Har bir qoidaga nechta quiz (default 1)")

    @transaction.atomic
    def handle(self, *args, **opts):
        clear = bool(opts["clear"])
        per_rule = int(opts["per_rule"])

        if clear:
            TajweedQuizOption.objects.all().delete()
            TajweedQuiz.objects.all().delete()

        rules = list(TajweedRule.objects.filter(is_published=True).order_by("id"))
        if len(rules) < 4:
            self.stdout.write(self.style.ERROR("Quiz uchun kamida 4 ta qoida kerak. Avval seed_tajweed ni run qiling."))
            return

        created = 0

        for rule in rules:
            for _ in range(per_rule):
                quiz, q_created = TajweedQuiz.objects.get_or_create(
                    rule=rule,
                    prompt=f"Quyidagi qaysi qoida? — {rule.title}",
                    defaults={"is_active": True},
                )
                if not q_created and quiz.options.exists():
                    continue

                # correct + 3 wrong
                wrong_rules = [r for r in rules if r.id != rule.id]
                wrongs = random.sample(wrong_rules, 3)

                options_text = [rule.title] + [w.title for w in wrongs]
                random.shuffle(options_text)

                for txt in options_text:
                    TajweedQuizOption.objects.create(
                        quiz=quiz,
                        text=txt,
                        is_correct=(txt == rule.title),
                    )

                created += 1

        self.stdout.write(self.style.SUCCESS(f"✅ Quiz ready. created={created}"))
