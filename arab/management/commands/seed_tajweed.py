from django.core.management.base import BaseCommand
from django.db import transaction

from arab.models import TajweedRule


RULES = [
    ("tajvid-ilmi", "1-dars: Tajvid ilmi", "Tajvid nima va hukmi",
     "Tajvid — Qur’on harflarini makhraj va sifatlarga rioya qilib o‘qish qoidalari. O‘rganish zarur bo‘lib, amalda to‘g‘ri tilovat qilishga xizmat qiladi.", "A0"),
    ("lahn", "2-dars: Lahn (xato tilovat)", "Tilovatdagi xatolar turlari",
     "Lahn — Qur’on o‘qishda xato qilish. Ochiq (ma’noni buzishi mumkin) va yashirin (qiroat tartibini buzadi) ko‘rinishlarda tushuntiriladi. Maqsad — xatoni kamaytirish va to‘g‘ri talaffuzni ushlash.", "A0"),
    ("qiroat-tezliklari", "3-dars: Qiroat tezliklari", "Tahqiq, hadr, tadvir",
     "Qiroat tezligi uch ko‘rinishda ishlatiladi: sekin va aniq o‘qish (tahqiq), o‘rtacha (tadvir), tez o‘qish (hadr). Har qanday holatda harf va qoidalar buzilmasligi shart.", "A0"),
    ("makhrajlar", "4-dars: Harflarning makhrajlari", "17 makhraj va 5 a’zo",
     "Makhraj — tovush chiqadigan joy. Amaliy tajvidda makhrajlar 17 ta deb o‘rgatiladi va ular og‘iz bo‘shlig‘i, halqum, til, lab va dimog‘ kabi asosiy a’zolarga taqsimlanadi.", "A1"),
    ("sifatlar", "5-dars: Harflarning sifatlari", "Zidli va zidsiz sifatlar",
     "Sifat — harf talaffuzidagi xususiyat. Ba’zilari zidli juft bo‘ladi, ba’zilari mustaqil. Sifatlarni bilish to‘g‘ri talaffuz va ravon tilovatga yordam beradi.", "A1"),
    ("ro-qoidalari", "6-dars: Ro (ر) harfi qoidalari", "Tafxim va tarqiq",
     "Ro harfi ba’zi holatlarda qalin (tafxim), ba’zi holatlarda ingichka (tarqiq) o‘qiladi. Ko‘pincha ro’ning harakati va atrofidagi tovushlar hisobga olinadi.", "A1"),
    ("lafzi-jalola", "7-dars: Lafzi Jalola", "Alloh lafzining o‘qilishi",
     "“Alloh” lafzi ko‘pincha undan oldingi harakatga qarab qalin yoki ingichka o‘qiladi: fatha/damma oldidan qalinroq, kasra oldidan ingichkaroq talaffuz qilinadi.", "A0"),
    ("nun-tanvin", "8-dars: Sukunli nun va tanvin", "Izhor, idg‘om, iqlob, ixfo",
     "Nun sokin va tanvin kelganda keyingi harfga qarab hukmlar bo‘ladi: izhor (aniq), idg‘om (qo‘shish), iqlob (aylantirish), ixfo (yashirish).", "A2"),
    ("mim-sukun", "9-dars: Sukunli mim", "Shafaviy hukmlar",
     "Mim sokin kelganda ham keyingi harfga qarab hukmlar bo‘ladi: izhor shafaviy (aniq), ixfo shafaviy (yashirish), idg‘om shafaviy (qo‘shish).", "A2"),
    ("mad-qoidalari", "10-dars: Mad qoidalari", "Cho‘zish turlari",
     "Mad — cho‘zib o‘qish. Tabiiy mad va sababli madlar (hamza/sukun/to‘xtash bilan bog‘liq) o‘rganiladi. Cho‘zish miqdori qoida turiga bog‘liq.", "A2"),
    ("idgom-turlari", "11-dars: Idg‘om turlari", "Mislayn, mutajonisayn, mutaqoribayn",
     "Idg‘om — ikki harfni talaffuzda qo‘shib yuborish. Harflar o‘xshashligiga qarab mislayn, mutajonisayn va mutaqoribayn kabi turlar o‘rganiladi.", "A2"),
    ("waqf-ibtido-sakta", "12-dars: Waqf, ibtido, sakta", "To‘xtash va boshlash qoidalari",
     "Waqf — to‘xtash, ibtido — qayta boshlash. Ma’no saqlanishi uchun to‘xtash joyi muhim. Sakta — juda qisqa pauza bo‘lib ayrim o‘rinlarda keladi.", "B1"),
    ("nabr", "13-dars: Nabr", "Urg‘u va ohang",
     "Nabr — o‘qishdagi urg‘u va ohangga oid tushuncha. Maqsad — talaffuzni ravon va tartilga mos qilish.", "B1"),
]


class Command(BaseCommand):
    help = "TajweedRule (1-13 dars) ni DBga seed qiladi (fixture xatosiz)."

    @transaction.atomic
    def handle(self, *args, **kwargs):
        created = 0
        updated = 0

        for slug, title, short_desc, explanation, level in RULES:
            obj, is_created = TajweedRule.objects.update_or_create(
                slug=slug,
                defaults={
                    "title": title,
                    "short_desc": short_desc,
                    "explanation": explanation,
                    "level": level,
                    "is_published": True,
                },
            )
            created += int(is_created)
            updated += int(not is_created)

        self.stdout.write(self.style.SUCCESS(f"✅ Done. created={created}, updated={updated}"))
