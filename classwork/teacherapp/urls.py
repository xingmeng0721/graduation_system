from django.urls import path
from .views import TeacherLoginView, TeacherProfileView

urlpatterns = [
    path('login/', TeacherLoginView.as_view(), name='student-login'),
    path('profile/', TeacherProfileView.as_view(), name='student-profile'),
]