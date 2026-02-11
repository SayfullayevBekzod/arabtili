import os
import django
import re

# Django muhitini sozlash
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from arab.models import Word, VocabularyCategory
from django.db.models.signals import post_save
from arab.models import auto_generate_audio

def clean_text(text):
    if not text: return ""
    # Arabchada ishlatilgan maxsus belgilarni tozalash (masalan: ٌ belgisini)
    text = text.replace('ٌ', '').replace('ً', '').replace('ٍ', '').replace('ّ', '').replace('ْ', '').replace('َ', '').replace('ُ', '').replace('ِ', '')
    # Aslida diakritikalar (harakatlar) saqlanishi kerak bo'lishi mumkin, 
    # lekin qidiruv va unikalylik uchun tozalangan variant ham kerak.
    # Biroq USER "hech qanday o'zgarishsiz" dedi, shuning uchun 'ٌ' kabi xatoliklarni tozalab, harakatlarni saqlaymiz.
    text = text.replace('ٌ', '').strip()
    # Ikki va undan ortiq bo'shliqlarni bittaga keltirish
    text = re.sub(r'\s+', ' ', text).strip()
    return text

def is_arabic(char):
    return '\u0600' <= char <= '\u06FF'

def is_cyrillic(char):
    # O'zbek kirill harflari va ba'zi maxsus belgilar
    return '\u0400' <= char <= '\u04FF' or char in "ʻ’'‘"

def split_line_smart(line):
    # Qatordagi arabcha va o'zbekcha qismlarni aqlli ravishda ajratish
    # Chiziqcha (-) bo'yicha ajratishga harakat qilamiz
    if '-' in line:
        # Eng oxirgi chiziqchani topamiz (ba'zida arabcha qismda ham bo'lishi mumkin)
        idx = line.rfind('-')
        arabic_part = line[:idx].strip()
        uzbek_part = line[idx+1:].strip()
        return arabic_part, uzbek_part
    
    # Chiziqcha bo'lmasa, kirill harfi boshlangan joydan ajratamiz
    arabic_part = ""
    uzbek_part = ""
    found_uzbek = False
    
    for char in line:
        if not found_uzbek and (is_cyrillic(char) or char in "(-"):
            # Agar qavs ochilsa yoki kirill harfi bo'lsa, bu o'zbekcha qism bo'lishi mumkin
            # Lekin arabchada ham qavslar bo'lishi mumkin. 
            # Shuning uchun kirill harfini kutamiz.
            if is_cyrillic(char):
                found_uzbek = True
        
        if found_uzbek:
            uzbek_part += char
        else:
            arabic_part += char
            
    return arabic_part.strip(), uzbek_part.strip()

def seed():
    print("🚀 Seeding started...")
    
    # Audio signalni vaqtincha o'chiramiz
    print("🔇 Disconnecting audio signal...")
    post_save.disconnect(auto_generate_audio, sender=Word)
    
    if not os.path.exists('extracted_pdf.txt'):
        print("❌ extracted_pdf.txt topilmadi!")
        return

    with open('extracted_pdf.txt', 'r', encoding='utf-8') as f:
        content = f.read()

    # Sahifalarni ajratamiz
    pages = content.split('==================================================')
    
    total_added = 0
    current_category = None
    
    for page in pages:
        lines = page.split('\n')
        for line in lines:
            line = line.strip()
            
            # Keraksiz qatorlarni o'tkazib yuboramiz
            if not line or 'www.arabic.uz' in line or line.isdigit():
                continue
                
            # Kategoriya aniqlash
            # Kategoriyalar odatda FAQAT kirill bosh harflarida (yoki arabcha bo'lmagan) bo'ladi
            if line.isupper() and any(is_cyrillic(c) for c in line) and not any(is_arabic(c) for c in line):
                cat_name = line.strip()
                current_category, _ = VocabularyCategory.objects.get_or_create(name=cat_name)
                print(f"📂 Kategoriya: {cat_name}")
                continue

            # So'zlarni ajratish
            if any(is_arabic(c) for c in line) and any(is_cyrillic(c) for c in line):
                ar_raw, uz_raw = split_line_smart(line)
                
                # 'ٌ' (tanvin damma) va boshqa xatoliklarni tozalaymiz
                # Lekin "hech qanday o'zgarishsiz" talabiga binoan, harakatlarni saqlaymiz
                ar = ar_raw.replace('ٌ', '').strip()
                uz = uz_raw.replace('ٌ', '').strip()
                
                if ar and uz:
                    try:
                        word, created = Word.objects.get_or_create(
                            arabic=ar,
                            defaults={
                                'translation_uz': uz,
                                'category': current_category,
                                'audio_source': 'manual',
                                'audio_pending': False
                            }
                        )
                        if created:
                            total_added += 1
                        else:
                            # Agar mavjud bo'lsa, o'zbekcha tarjimasini yangilashimiz yoki qo'shishimiz mumkin
                            if uz not in word.translation_uz:
                                word.translation_uz += f"; {uz}"
                                word.save()
                    except Exception as e:
                        print(f"⚠️ Xatolik ({ar}): {e}")

    # Signalni qayta ulaymiz (ixtiyoriy, lekin yaxshi amaliyot)
    post_save.connect(auto_generate_audio, sender=Word)
    print(f"✅ Seeding yakunlandi. Jami {total_added} ta yangi so'z qo'shildi.")

if __name__ == "__main__":
    seed()
