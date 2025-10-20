from django.urls import path
from .views import StudentLoginView, StudentProfileView

urlpatterns = [
    path('login/', StudentLoginView.as_view(), name='student-login'),
    path('profile/', StudentProfileView.as_view(), name='student-profile'),
]