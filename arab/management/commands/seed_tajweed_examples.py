from django.core.management.base import BaseCommand
from django.db import transaction

from arab.models import TajweedRule, TajweedExample


EXAMPLES = {
    # slug: [(arabic, uz_translation), ...]
    "tajvid-ilmi": [
        ("الْحَمْدُ لِلَّهِ", "Hamd Alloh uchundir."),
        ("رَبِّ الْعَالَمِينَ", "Olamlar Parvardigori."),
        ("اهْدِنَا الصِّرَاطَ الْمُسْتَقِيمَ", "Bizni to‘g‘ri yo‘lga hidoyat qil."),
    ],
    "lahn": [
        ("قُلْ هُوَ اللَّهُ أَحَدٌ", "Ayting: U — Alloh Yagonadir."),
        ("مَالِكِ يَوْمِ الدِّينِ", "Din kuni Egasi."),
        ("وَإِيَّاكَ نَسْتَعِينُ", "Yolg‘iz Sendangina yordam so‘raymiz."),
    ],
    "qiroat-tezliklari": [
        ("وَاللَّهُ غَفُورٌ رَحِيمٌ", "Alloh Mag‘firatli va Rahmlidir."),
        ("إِنَّ اللَّهَ عَلِيمٌ حَكِيمٌ", "Alloh Bilguvchi va Hikmatlidir."),
        ("وَهُوَ السَّمِيعُ الْبَصِيرُ", "U Eshituvchi va Ko‘ruvchidir."),
    ],
    "makhrajlar": [
        ("أَ", "Hamza (halqumdan chiqadi)."),
        ("ح", "Ha’ (halqum o‘rta qismi)."),
        ("ق", "Qof (til orqa qismi)."),
        ("ف", "Fa (lab/old tishlar)."),
    ],
    "sifatlar": [
        ("قَدْ", "Qalqala bo‘lishi mumkin bo‘lgan harf bilan misol."),
        ("أَتَى", "Hams/jahr sifati amaliyoti uchun misol."),
        ("صِرَاطَ", "Isti’lo/istifol sifatlariga misol bo‘lishi mumkin."),
    ],
    "ro-qoidalari": [
        ("رَبِّ", "Ro’ holatiga e’tibor (qalin/ingichka)."),
        ("قَرِيبٌ", "Ro’ kasra atrofida ingichka bo‘lishi mumkin."),
        ("غَفُورٌ", "Ro’ damma bilan qalin bo‘lishi mumkin."),
    ],
    "lafzi-jalola": [
        ("اللَّهُ", "Lafzi jalola talaffuzi (oldingi harakatga bog‘liq)."),
        ("بِاللَّهِ", "Kasra oldidan ingichkaroq holat bo‘lishi mumkin."),
        ("وَاللَّهُ", "Fatha/damma oldidan qalinroq holat bo‘lishi mumkin."),
    ],
    "nun-tanvin": [
        ("مِنْ هَادٍ", "Nun sokin: izhor misoli bo‘lishi mumkin."),
        ("مِنْ رَبِّهِمْ", "Nun sokin: idg‘om/ixfo holatlari mashqi uchun."),
        ("عَلِيمٌ خَبِيرٌ", "Tanvin: ixfo/izhor mashqi uchun."),
        ("مِنْ بَعْدِ", "Iqlob bo‘lishi mumkin bo‘lgan holatlar uchun mashq."),
    ],
    "mim-sukun": [
        ("هُمْ مُّؤْمِنُونَ", "Mim sokin: idg‘om shafaviy bo‘lishi mumkin."),
        ("عَلَيْهِمْ بِهِ", "Mim sokin: ixfo shafaviy bo‘lishi mumkin."),
        ("لَهُمْ فِيهَا", "Mim sokin: izhor shafaviy bo‘lishi mumkin."),
    ],
    "mad-qoidalari": [
        ("قَالَ", "Mad tabiiy (2 harakat)."),
        ("جَاءَ", "Hamza bilan bog‘liq mad (muttasil bo‘lishi mumkin)."),
        ("فِي أَنْفُسِكُمْ", "Mad + hamza boshqa so‘zda (munfasil bo‘lishi mumkin)."),
        ("الضَّالِّينَ", "Sukun/lozim bilan bog‘liq cho‘zish misoli bo‘lishi mumkin."),
    ],
    "idgom-turlari": [
        ("قَدْ تَّبَيَّنَ", "Idg‘om holatlari mashqi uchun."),
        ("مِن لَّدُنْهُ", "Idg‘om bilan mashq bo‘lishi mumkin."),
        ("أَحَدٌ صَمَدٌ", "Tanvin + harf holati mashqi uchun."),
    ],
    "waqf-ibtido-sakta": [
        ("وَقِيلَ مَنْ رَاقٍ", "Waqf/ibtido mashqi uchun jumla."),
        ("كَلَّا بَلْ ۜ", "Sakta bo‘lishi mumkin bo‘lgan belgi bilan mashq (umumiy)."),
        ("وَاللَّهُ أَعْلَمُ", "To‘xtash va qayta boshlash mashqi."),
    ],
    "nabr": [
        ("إِيَّاكَ نَعْبُدُ", "Ohang/urg‘u mashqi."),
        ("وَإِيَّاكَ نَسْتَعِينُ", "Urg‘u va ravonlik mashqi."),
        ("اهْدِنَا الصِّرَاطَ الْمُسْتَقِيمَ", "Ritm va urg‘u mashqi."),
    ],
}


class Command(BaseCommand):
    help = "Har bir TajweedRule uchun arabcha misollarni seed qiladi (TajweedExample)."

    def add_arguments(self, parser):
        parser.add_argument("--clear", action="store_true", help="Oldingi misollarni o‘chirib qayta qo‘yadi")

    @transaction.atomic
    def handle(self, *args, **opts):
        clear = bool(opts["clear"])

        created = 0
        skipped = 0
        cleared = 0

        for slug, items in EXAMPLES.items():
            try:
                rule = TajweedRule.objects.get(slug=slug)
            except TajweedRule.DoesNotExist:
                self.stdout.write(self.style.WARNING(f"Skip: rule topilmadi: {slug}"))
                continue

            if clear:
                c = rule.examples.all().delete()[0]
                cleared += c

            for arabic, tr in items:
                if TajweedExample.objects.filter(rule=rule, arabic_text=arabic).exists():
                    skipped += 1
                    continue
                TajweedExample.objects.create(rule=rule, arabic_text=arabic, translation_uz=tr)
                created += 1

        if clear:
            self.stdout.write(self.style.SUCCESS(f"✅ Done. cleared={cleared}, created={created}, skipped={skipped}"))
        else:
            self.stdout.write(self.style.SUCCESS(f"✅ Done. created={created}, skipped={skipped}"))
