"""
SQLite dan PostgreSQL ga ma'lumotlarni ko'chirish scripti
"""
import os
import django
import json

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.core import serializers
from arab.models import (
    Word, VocabularyCategory, Letter, Course, Unit, Lesson,
    TajweedRule, TajweedExample, TajweedTag, UserGamification,
    UserWordProgress, UserStreak, UserDailyStat, Homework,
    Pronunciation, LetterExample, LessonSection, Exercise, Question,
    PlacementQuestion, PlacementOption, WordExample, GrammarRule, Diacritic
)

def export_to_json():
    """Barcha ma'lumotlarni JSON ga eksport qilish"""
    
    print("📦 Ma'lumotlarni eksport qilish boshlandi...")
    
    # Eksport qilinadigan modellar
    models_to_export = [
        ('VocabularyCategory', VocabularyCategory),
        ('Word', Word),
        ('Letter', Letter),
        ('Pronunciation', Pronunciation), # Added
        ('LetterExample', LetterExample), # Added
        ('Course', Course),
        ('Unit', Unit),
        ('Lesson', Lesson),
        ('LessonSection', LessonSection), # Added
        ('Exercise', Exercise), # Added
        ('Question', Question), # Added
        ('PlacementQuestion', PlacementQuestion), # Added
        ('PlacementOption', PlacementOption), # Added
        ('WordExample', WordExample), # Added
        ('Diacritic', Diacritic), # Added
        ('GrammarRule', GrammarRule), # Added
        ('TajweedRule', TajweedRule),
        ('TajweedTag', TajweedTag),
        ('TajweedExample', TajweedExample),
        ('Homework', Homework),
    ]
    
    all_data = []
    stats = {}
    
    for name, model in models_to_export:
        objects = model.objects.all()
        count = objects.count()
        stats[name] = count
        
        if count > 0:
            print(f"  ✓ {name}: {count} ta")
            serialized = serializers.serialize('json', objects, indent=2, use_natural_foreign_keys=True)
            data = json.loads(serialized)
            all_data.extend(data)
    
    # Faylga yozish
    output_file = 'database_export.json'
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(all_data, f, ensure_ascii=False, indent=2)
    
    print(f"\n✅ Eksport yakunlandi!")
    print(f"📁 Fayl: {output_file}")
    print(f"📊 Jami: {len(all_data)} ta obyekt")
    print("\n📋 Tafsilotlar:")
    for name, count in stats.items():
        print(f"   • {name}: {count}")
    
    return output_file

def import_from_json(filename='database_export.json'):
    """JSON dan ma'lumotlarni import qilish (PostgreSQL uchun)"""
    from django.db import IntegrityError
    
    print(f"\n📥 {filename} dan import qilish boshlandi...")
    
    if not os.path.exists(filename):
        print(f"❌ Fayl topilmadi: {filename}")
        return
    
    with open(filename, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    print(f"🔍 {len(data)} ta obyekt topildi")
    
    # Import with duplicate handling
    imported = 0
    skipped = 0
    errors = 0
    
    for obj in serializers.deserialize('json', json.dumps(data)):
        try:
            obj.save()
            imported += 1
        except IntegrityError:
            # Object already exists, skip it
            skipped += 1
        except Exception as e:
            errors += 1
            print(f"⚠️ Xatolik: {e}")
    
    print(f"✅ Import yakunlandi! Imported: {imported}, Skipped: {skipped}, Errors: {errors}")

if __name__ == '__main__':
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == 'import':
        # Import rejimi
        filename = sys.argv[2] if len(sys.argv) > 2 else 'database_export.json'
        import_from_json(filename)
    else:
        # Eksport rejimi (default)
        export_to_json()
        print("\n💡 PostgreSQL ga yuklash uchun:")
        print("   python migrate_to_postgres.py import database_export.json")
