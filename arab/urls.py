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
    path("review/", views.review, name="review"),
    path("dictionary/", views.dictionary, name="dictionary"),
    path("progress/", views.progress, name="progress"),

    path("accounts/register/", views.register, name="register"),
    path("accounts/login/", views.login_view, name="login"),
    path("accounts/logout/", views.logout_view, name="logout"),
    
    path("exercises/<int:pk>/", views.exercise_run, name="exercise_run"),
    path("exercises/<int:pk>/submit/", views.exercise_submit, name="exercise_submit"),

    path("review/grade/<int:card_id>/<int:grade>/", views.review_grade, name="review_grade"),
    path("tajweed/quiz/", views.tajweed_quiz, name="tajweed_quiz"),
    path("tajweed/", views.tajweed_index, name="tajweed_index"),
    path("tajweed/<slug:slug>/", views.tajweed_detail, name="tajweed_detail"),
    path("tajweed/quiz/", views.tajweed_quiz_live, name="tajweed_quiz"),
    path("progress/", views.progress, name="progress"),

]
