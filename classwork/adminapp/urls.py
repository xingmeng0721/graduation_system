from django.urls import path, include
from .views import RegisterView, LoginView, BulkRegisterView, DownloadTemplateView, AdminUserListView, MajorListView, \
    GroupListView
from rest_framework_simplejwt.views import TokenRefreshView
from rest_framework.routers import DefaultRouter
from .views import (
    LoginView,
    AdminUserListView,
    StudentManagementViewSet # 导入 ViewSet
)

router = DefaultRouter()
router.register(r'students', StudentManagementViewSet, basename='student-management')

urlpatterns = [
    # 注册 API
    path('register/', RegisterView.as_view(), name='register'),

    # 登录 API
    path('login/', LoginView.as_view(), name='login'),

    # simple-jwt 提供的用于刷新 access token 的接口
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),

    # 批量注册 API
    path('register/bulk/', BulkRegisterView.as_view(), name='bulk-register'),

    # 下载模板 API
    path('register/template/', DownloadTemplateView.as_view(), name='download-template'),

    # 管理员查看用户列表 API
    path('users/', AdminUserListView.as_view(), name='user-list'),

    # 学生管理的 ViewSet 路由
    path('', include(router.urls)),
    path('majors/', MajorListView.as_view(), name='major-list'),
    path('groups/', GroupListView.as_view(), name='group-list'),
]