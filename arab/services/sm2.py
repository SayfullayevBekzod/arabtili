from django.utils import timezone

def sm2_update(card, quality: int):
    """
    quality: 0..5
      5 - juda oson
      4 - yaxshi
      3 - zo'rg'a
      2..0 - xato (qaytadan)
    """
    quality = max(0, min(5, int(quality)))

    # minimal ease factor
    if card.ease_factor is None:
        card.ease_factor = 2.5

    if quality < 3:
        card.repetitions = 0
        card.interval_days = 1
    else:
        if card.repetitions == 0:
            card.interval_days = 1
        elif card.repetitions == 1:
            card.interval_days = 6
        else:
            card.interval_days = int(round(card.interval_days * card.ease_factor))

        card.repetitions += 1

    # EF update
    card.ease_factor = card.ease_factor + (0.1 - (5 - quality) * (0.08 + (5 - quality) * 0.02))
    if card.ease_factor < 1.3:
        card.ease_factor = 1.3

    card.due_at = timezone.now() + timezone.timedelta(days=card.interval_days)
    return card
