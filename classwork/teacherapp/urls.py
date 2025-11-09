from django.urls import path
from .views import TeacherLoginView, TeacherProfileView, refresh_teacher_token

urlpatterns = [
    path('login/', TeacherLoginView.as_view(), name='student-login'),
    path('profile/', TeacherProfileView.as_view(), name='student-profile'),
    path('token/refresh/', refresh_teacher_token, name='teacher_token_refresh'),
]