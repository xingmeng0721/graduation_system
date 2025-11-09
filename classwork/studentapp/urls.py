from django.urls import path
from .views import StudentLoginView, StudentProfileView, SendResetCodeView, ResetPasswordByCodeView, refresh_student_token

urlpatterns = [
    path('login/', StudentLoginView.as_view(), name='student-login'),
    path('profile/', StudentProfileView.as_view(), name='student-profile'),
    path('reset-code/', ResetPasswordByCodeView.as_view(), name='student-reset-code'),
    path('send-reset-code/', SendResetCodeView.as_view(), name='student-send-reset-code'),
    path('token/refresh/', refresh_student_token, name='student_token_refresh'),
]