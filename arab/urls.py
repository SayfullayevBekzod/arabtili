from django.urls import path
from . import views

app_name = "arab"

urlpatterns = [
    path("", views.home, name="home"),
    path("roadmap/", views.roadmap, name="roadmap"),

    path("alphabet/", views.alphabet, name="alphabet"),
    path("letters/<int:pk>/", views.letter_detail, name="letter_detail"),
    path("letters/<int:pk>/practice/", views.letter_practice, name="letter_practice"),

    path("courses/", views.course_list, name="course_list"),
    path("courses/<int:pk>/", views.course_detail, name="course_detail"),
    path("lessons/<int:pk>/", views.lesson_detail, name="lesson_detail"),

    path("practice/", views.practice_hub, name="practice"),
    path("practice/weak/", views.practice_weak_words, name="practice_weak_words"),
    path("review/", views.review, name="review"),
    path("dictionary/", views.dictionary, name="dictionary"),
    path("progress/", views.progress, name="progress"),
    path("api/stats/live/", views.get_live_stats, name="api_live_stats"),
    path("api/study-time/update/", views.update_study_time, name="api_study_time_update"),
    path("practice/match/", views.practice_match_game, name="practice_match_game"),
    path("api/match/reward/", views.api_match_reward, name="api_match_reward"),

    path("accounts/register/", views.register, name="register"),
    path("accounts/login/", views.login_view, name="login"),
    path("login/", views.login_view, name="login_direct"),
    path("accounts/logout/", views.logout_view, name="logout"),

    
    path("exercises/<int:pk>/", views.exercise_run, name="exercise_run"),
    path("exercises/<int:pk>/submit/", views.exercise_submit, name="exercise_submit"),

    path("lessons/video/<int:pk>/", views.video_detail, name="video_detail"),
    path("lessons/video/<int:pk>/progress/", views.video_progress, name="video_progress"),
    path("videos/", views.video_library, name="video_library"),

    path("review/grade/<int:card_id>/<int:grade>/", views.review_grade, name="review_grade"),
    path("tajweed/", views.tajweed_index, name="tajweed_index"),
    path("tajweed/logic-tree/", views.tajweed_logic_tree, name="tajweed_logic_tree"),
    path("tajweed/pro-drill/", views.tajweed_pro_drill, name="tajweed_pro_drill"),
    path("tajweed/whiteboard/", views.tajweed_whiteboard, name="tajweed_whiteboard"),
    path("tajweed/quiz/", views.tajweed_quiz, name="tajweed_quiz"),
    path("tajweed/live-quiz/", views.tajweed_quiz_live, name="tajweed_quiz_live"),
    path("tajweed/<slug:slug>/", views.tajweed_detail, name="tajweed_detail"),
    
    path("quran/", views.quran_index, name="quran_index"),
    path("quran/<int:surah_number>/", views.quran_detail, name="quran_detail"),

    path("placement/", views.placement_test, name="placement"),

    path("dictionary/add/<int:word_id>/", views.dictionary_add_card, name="dictionary_add_card"),
    path("settings/profile/", views.settings_profile, name="settings_profile"),
    path("settings/password/", views.settings_password, name="settings_password"),
]
