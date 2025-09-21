from django.urls import path
from . import views

urlpatterns = [
    # 认证相关
    path('register/', views.RegisterView.as_view(), name='register'),
    path('login/', views.LoginView.as_view(), name='login'),
    path('logout/', views.LogoutView.as_view(), name='logout'),
    path('profile/', views.ProfileView.as_view(), name='profile'),
    path('current-user/', views.current_user_view, name='current-user'),
    path('change-password/', views.PasswordChangeView.as_view(), name='change-password'),
    
    # 档案相关
    path('student-profile/', views.StudentProfileView.as_view(), name='student-profile'),
    path('teacher-profile/', views.TeacherProfileView.as_view(), name='teacher-profile'),
    
    # 用户列表
    path('teachers/', views.TeacherListView.as_view(), name='teacher-list'),
    path('students/', views.StudentListView.as_view(), name='student-list'),
]