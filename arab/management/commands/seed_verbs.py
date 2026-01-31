"""
Management command to seed Arabic verbs with moziy, mudoriy, and amr forms
Updates both ArabicVerb and VerbConjugation models.
"""
from django.core.management.base import BaseCommand
from arab.models import ArabicVerb, VerbConjugation


VERBS_DATA = [
    # (past, present, command, translation_uz)
    ("مَدَحَ", "يَمْدَحُ", "اِمْدَحْ", "Maqtadi"),
    ("كَتَبَ", "يَكْتُبُ", "اُكْتُبْ", "Yozdi"),
    ("قَرَأَ", "يَقْرَأُ", "اِقْرَأْ", "O'qidi"),
    ("مَنَحَ", "يَمْنَحُ", "اِمْنَحْ", "Berdi (Hadya qildi)"),
    ("أَخَذَ", "يَأْخُذُ", "خُذْ", "Oldi"),
    ("سَرَقَ", "يَسْرِقُ", "اِسْرِقْ", "O'g'irladi"),
    ("أَكَلَ", "يَأْكُلُ", "كُلْ", "Yedi"),
    ("فَتَحَ", "يَفْتَحُ", "اِفْتَحْ", "Ochdi"),
    ("جَمَعَ", "يَجْمَعُ", "اِجْمَعْ", "To'pladi"),
    ("رَحَلَ", "يَرْحَلُ", "اِرْحَلْ", "Ko'chdi (Jo'nadi)"),
    ("سَكَنَ", "يَسْكُنُ", "اُسْكُنْ", "Yashadi (Turdi)"),
    ("رَجَعَ", "يَرْجِعُ", "اِرْجِعْ", "Qaytdi"),
    ("ذَهَبَ", "يَذْهَبُ", "اِذْهَبْ", "Ketdi"),
    ("دَخَلَ", "يَدْخُلُ", "اُدْخُلْ", "Kirdi"),
    ("خَرَجَ", "يَخْرُجُ", "اُخْرُجْ", "Chiqdi"),
    ("رَقَدَ", "يَرْقُدُ", "اُرْقُدْ", "Uxladi (Yotdi)"),
    ("جَلَسَ", "يَجْلِسُ", "اِجْلِسْ", "O'tirdi"),
    ("تَرَكَ", "يَتْرُكُ", "اُتْرُكْ", "Tark qildi"),
    ("نَظَرَ", "يَنْظُرُ", "اُنْظُرْ", "Qaradi"),
    ("ضَرَبَ", "يَضْرِبُ", "اِضْرِبْ", "Urdi"),
    ("شَتَمَ", "يَشْتِمُ", "اِشْتِمْ", "So'kdi"),
    ("عَرَفَ", "يَعْرِفُ", "اِعْرِفْ", "Tanidi"),
    ("حَسِبَ", "يَحْسَبُ", "اِحْسَبْ", "O'yladi (Hisobladi)"),
    ("عَلِمَ", "يَعْلَمُ", "اِعْلَمْ", "Bildi"),
    ("فَهِمَ", "يَفْهَمُ", "اِفْهَمْ", "Tushundi"),
    ("سَمِعَ", "يَسْمَعُ", "اِسْمَعْ", "Eshitdi"),
    ("شَرِبَ", "يَشْرَبُ", "اِشْرَبْ", "Ichdi"),
    ("لَبِسَ", "يَلْبَسُ", "اِلْبَسْ", "Kiydi"),
    ("حَفِظَ", "يَحْفَظُ", "اِحْفَظْ", "Yodladi (Saqladi)"),
    ("فَرِحَ", "يَفْرَحُ", "اِفْرَحْ", "Xursand bo'ldi"),
    ("ضَحِكَ", "يَضْحَكُ", "اِضْحَكْ", "Kuldi"),
    ("نَدِمَ", "يَنْدَمُ", "اِنْدَمْ", "Nadomat qildi"),
    ("لَعِبَ", "يَلْعَبُ", "اِلْعَبْ", "O'ynadi"),
    ("بَصُرَ", "يَبْصُرُ", "اُبْصُرْ", "Ko'rdi"),
    ("قَرُبَ", "يَقْرُبُ", "اُقْرُبْ", "Yaqin bo'ldi"),
    ("بَعُدَ", "يَبْعُدُ", "اُبْعُدْ", "Uzoq bo'ldi"),
    ("كَبُرَ", "يَكْبُرُ", "اُكْبُرْ", "Katta bo'ldi"),
    ("صَغُرَ", "يَصْغُرُ", "اُصْغُرْ", "Kichik bo'ldi"),
    ("كَثُرَ", "يَكْثُرُ", "اُكْثُرْ", "Ko'paydi"),
    ("قَلَّ", "يَقِلُّ", "أَقْلِلْ", "Ozaydi"),
    ("حَسُنَ", "يَحْسُنُ", "اُحْسُنْ", "Chiroyli bo'ldi"),
    ("قَبُحَ", "يَقْبُحُ", "اُقْبُحْ", "Xunuk bo'ldi"),
    ("سَهُلَ", "يَسْهُلُ", "اُسْهُلْ", "Oson bo'ldi"),
    ("صَعُبَ", "يَصْعُبُ", "اُصْعُبْ", "Qiyin bo'ldi"),
    ("نَطَقَ", "يَنْطِقُ", "اِنْطِقْ", "Gapirdi"),
    ("سَعَلَ", "يَسْعُلُ", "اُسْعُلْ", "Yo'taldi"),
    ("عَطَسَ", "يَعْطِسُ", "اِعْطِسْ", "Aksa urdi"),
    ("سَأَلَ", "يَسْأَلُ", "اِسْأَلْ", "So'radi"),
    ("طَمَعَ", "يَطْمَعُ", "اِطْمَعْ", "Tama' qildi"),
    ("قَنَعَ", "يَقْنَعُ", "اِقْنَاعْ", "Qanoat qildi"),
    ("حَمَلَ", "يَحْمِلُ", "اِحْمِلْ", "Ko'tardi"),
    ("خَدَمَ", "يَخْدِمُ", "اِخْدِمْ", "Xizmat qildi"),
    ("قَطَعَ", "يَقْطَعُ", "اِقْطَعْ", "Kesdi"),
    ("خَدَمَ", "يَخْدِمُ", "اِخْدِمْ", "Xizmat qildi"), # Duplicate translation in data but harmless
    ("قَطَعَ", "يَقْطَعُ", "اِقْطَعْ", "Kesdi"),
    ("خَدَعَ", "يَخْدَعُ", "اِخْدَعْ", "Aldadi"),
    ("فَعَلَ", "يَفْعَلُ", "اِفْعَلْ", "Bajardi (Qildi)"),
    ("طَرَحَ", "يَطْرَحُ", "اِطْرَحْ", "Tashladi"),
    ("صَبَرَ", "يَصْبِرُ", "اِصْبِرْ", "Sabr qildi"),
    ("عَجِلَ", "يَعْجَلُ", "اِعْجَلْ", "Shoshildi"),
    ("خَلَقَ", "يَخْلُقُ", "اُخْلُقْ", "Yaratdi"),
    ("رَزَقَ", "يَرْزُقُ", "اُرْزُقْ", "Rizq berdi"),
    ("شَكَرَ", "يَشْكُرُ", "اُشْكُرْ", "Shukur qildi"),
    ("عَبَدَ", "يَعْبُدُ", "اُعْبُدْ", "Ibodat qildi"),
    ("طَلَبَ", "يَطْلُبُ", "اُطْلُبْ", "Talab qildi (Izladi)"),
    ("أَمَرَ", "يَأْمُرُ", "مُرْ", "Buyurdi"),
    ("نَهَى", "يَنْهَى", "اِنْهَ", "Qaytardi"),
    ("بَعَثَ", "يَبْعَثُ", "اِبْعَثْ", "Yubordi"),
    ("نَزَلَ", "يَنْزِلُ", "اِنْزِلْ", "Tushdi"),
    ("أَنْزَلَ", "يُنْزِلُ", "أَنْزِلْ", "Tushirdi"),
    ("زَعَمَ", "يَزْعُمُ", "اِزْعُمْ", "Gumon qildi"),
    ("كَذَبَ", "يَكْذِبُ", "اِكْذِبْ", "Yolg'on gapirdi"),
    ("صَدَقَ", "يَصْدُقُ", "اُصْدُقْ", "Rost gapirdi"),
    ("قَالَ", "يَقُولُ", "قُلْ", "Aytdi"),
    ("جَاءَ", "يَجِيءُ", "جِئْ", "Keldi"),
    ("شَاءَ", "يَشَاءُ", "شَأْ", "Xohladi"),
    ("أَرَادَ", "يُرِيدُ", "أَرِدْ", "Istadi"),
    ("أَحَبَّ", "يُحِبُّ", "أَحِبَّ", "Yaxshi ko'rdi"),
    ("أَبْغَضَ", "يُبْغِضُ", "أَبْغِضْ", "Yomon ko'rdi"),
]


class Command(BaseCommand):
    help = 'Seed Arabic verbs with moziy, mudoriy, and amr forms into ArabicVerb and VerbConjugation models'

    def handle(self, *args, **options):
        verb_created_count = 0
        verb_updated_count = 0
        conj_total_count = 0
        
        for past, present, command, translation in VERBS_DATA:
            # 1. Update or Create ArabicVerb
            verb, created = ArabicVerb.objects.update_or_create(
                past_base=past,
                defaults={
                    'present_base': present,
                    'command_base': command,
                    'translation_uz': translation,
                    'verb_form': '1',
                }
            )
            
            if created:
                verb_created_count += 1
            else:
                verb_updated_count += 1
                
            # 2. Create VerbConjugations for practice session
            # Moziy (3rd person masc singular - Huwa)
            VerbConjugation.objects.update_or_create(
                verb=verb,
                tense="past",
                person="3ms",
                defaults={'conjugated_form': past}
            )
            
            # Mudori (3rd person masc singular - Huwa)
            VerbConjugation.objects.update_or_create(
                verb=verb,
                tense="present",
                person="3ms",
                defaults={'conjugated_form': present}
            )
            
            # Amr (2nd person masc singular - Anta)
            VerbConjugation.objects.update_or_create(
                verb=verb,
                tense="command",
                person="2ms",
                defaults={'conjugated_form': command}
            )
            
            conj_total_count += 3
        
        self.stdout.write(self.style.SUCCESS(
            f"Done! {verb_created_count} verbs created, {verb_updated_count} updated. "
            f"Total {conj_total_count} conjugations seeded."
        ))
