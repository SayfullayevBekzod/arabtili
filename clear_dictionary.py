import os
import django

# Django muhitini sozlash
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from arab.models import Word

def clear_words():
    print("🧹 Lug'atdagi barcha so'zlarni o'chirish boshlandi...")
    
    # Word modelidagi barcha obyektlarni o'chirish
    # Bu WordExample, UserWordProgress kabi bog'langan (CASCADE) obyektlarni ham o'chiradi
    count = Word.objects.count()
    if count == 0:
        print("✅ Lug'at allaqachon bo'sh.")
        return

    Word.objects.all().delete()
    print(f"✅ {count} ta so'z o'chirildi.")
    print("🚀 Lug'at tozalandi.")

if __name__ == "__main__":
    clear_words()
