import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from arab.models import ScenarioCategory, Scenario, DialogLine, PhrasebookEntry

def seed_scenarios():
    # 1. Categories
    cat_daily, _ = ScenarioCategory.objects.get_or_create(
        name="Kundalik muloqot", 
        icon="fas fa-home", 
        order=1
    )
    cat_travel, _ = ScenarioCategory.objects.get_or_create(
        name="Sayohat", 
        icon="fas fa-plane", 
        order=2
    )
    cat_shop, _ = ScenarioCategory.objects.get_or_create(
        name="Bozor va Xarid", 
        icon="fas fa-shopping-bag", 
        order=3
    )

    # 2. Scenarios
    sc_intro, _ = Scenario.objects.get_or_create(
        category=cat_daily,
        title="Tanishuv",
        description="Birinchi marta ko'rishganda muloqot qilishni o'rganing.",
        difficulty="beginner",
        xp_reward=50
    )

    sc_market, _ = Scenario.objects.get_or_create(
        category=cat_shop,
        title="Bozorda",
        description="Narx so'rash va savdolashishni o'rganing.",
        difficulty="beginner",
        xp_reward=75
    )

    # 3. Dialog Lines for Intro
    DialogLine.objects.all().filter(scenario=sc_intro).delete()
    DialogLine.objects.create(
        scenario=sc_intro, character_name="Ahmad", order=1,
        text_arabic="السلام عليكم ورحمة الله وبركاته",
        text_uz="Assalomu alaykum va rohmatullohi va barokatuh",
        text_ru="Мир вам, милость Аллаха и Его благословение",
        transliteration="As-salamu alaykum wa rahmatullahi wa barakatuh"
    )
    DialogLine.objects.create(
        scenario=sc_intro, character_name="Sami", order=2,
        text_arabic="وعليكم السلام ورحمة الله وبركاته. أهلاً وسهلاً",
        text_uz="Va alaykum assalom va rohmatullohi va barokatuh. Xush kelibsiz!",
        text_ru="И вам мир, милость Аллаха и Его благословение. Добро пожаловать!",
        transliteration="Wa alaykum as-salam wa rahmatullahi wa barakatuh. Ahlan wa sahlan"
    )
    DialogLine.objects.create(
        scenario=sc_intro, character_name="Ahmad", order=3,
        text_arabic="كيف حالك؟ ما اسمك؟",
        text_uz="Ahvoling qanday? Isming nima?",
        text_ru="Как дела? Как тебя зовут?",
        transliteration="Kayfa haluk? Masmuk?"
    )
    DialogLine.objects.create(
        scenario=sc_intro, character_name="Sami", order=4, is_user_line=True,
        text_arabic="أنا بخير الحمد لله. اسمي سامي. وأنت؟",
        text_uz="Yaxshiman, Allohga shukr. Ismim Sami. O'zingizniki-chi?",
        text_ru="Хорошо, слава Аллаху. Меня зовут Сами. А тебя?",
        transliteration="Ana bikhayr alhamdu lillah. Ismi Sami. Wa anta?"
    )

    # 4. Phrasebook Entries
    PhrasebookEntry.objects.get_or_create(
        category=cat_daily,
        text_arabic="صباح الخير",
        text_uz="Xayrli tong",
        text_ru="Доброе утро",
        transliteration="Sabah al-khayr"
    )
    PhrasebookEntry.objects.get_or_create(
        category=cat_daily,
        text_arabic="مساء الخير",
        text_uz="Xayrli kech",
        text_ru="Добрый вечер",
        transliteration="Masa al-khayr"
    )
    PhrasebookEntry.objects.get_or_create(
        category=cat_shop,
        text_arabic="بكم هذا؟",
        text_uz="Bu necha pul?",
        text_ru="Сколько это стоит?",
        transliteration="Bikam hadha?"
    )

    print("Conversational data seeded successfully!")

if __name__ == "__main__":
    seed_scenarios()
