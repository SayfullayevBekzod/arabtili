# arab/services/question_generator.py
import random
from arab.models import Diacritic, Question, Choice

def generate_diacritic_question(exercise, word: str):
    diacritics = list(Diacritic.objects.all())
    correct = random.choice(diacritics)

    q = Question.objects.create(
        exercise=exercise,
        text=f"Quyidagi so‘zda qaysi harakat bor: {word}",
        explanation=f"To‘g‘ri javob: {correct.key}"
    )

    options = random.sample(diacritics, 4)
    if correct not in options:
        options[0] = correct

    for d in options:
        Choice.objects.create(
            question=q,
            text=d.key,
            is_correct=(d == correct)
        )
