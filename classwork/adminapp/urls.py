from django.urls import path, include
from .views import RegisterView, LoginView, BulkRegisterView, DownloadTemplateView, MajorListView, TeacherManagementViewSet, MutualSelectionEventViewSet, BulkRegisterTeachersView,DownloadTeacherTemplateView
from rest_framework_simplejwt.views import TokenRefreshView
from rest_framework.routers import DefaultRouter
from .views import (
    LoginView,
    AdminUserManagementViewSet,
    AdminProfileView,
    StudentManagementViewSet,
    DownloadStudentTemplateView,
    BulkRegisterStudentsView,
    refresh_admin_token,
)

router = DefaultRouter()
router.register(r'students', StudentManagementViewSet, basename='student-management')
router.register(r'teachers', TeacherManagementViewSet, basename='teacher-management')
router.register(r'users', AdminUserManagementViewSet, basename='admin-user-management')

mutual_selection_list = MutualSelectionEventViewSet.as_view({
    'get': 'list',    # GET 请求映射到 list 方法 (获取列表)
    'post': 'create'  # POST 请求映射到 create 方法 (创建新条目)
})

mutual_selection_detail = MutualSelectionEventViewSet.as_view({
    'get': 'retrieve',      # GET 请求映射到 retrieve 方法 (获取单个详情)
    'put': 'update',        # PUT 请求映射到 update 方法 (完整更新)
    'patch': 'partial_update', # PATCH 请求映射到 partial_update 方法 (部分更新)
    'delete': 'destroy'     # DELETE 请求映射到 destroy 方法 (删除)
})

# 自定义 action (如 bulk_delete) 需要单独定义
mutual_selection_bulk_delete = MutualSelectionEventViewSet.as_view({
    'post': 'bulk_delete' # POST 请求映射到 bulk_delete 方法
})

mutual_selection_auto_assign = MutualSelectionEventViewSet.as_view({
    'post': 'auto_assign'  # POST 请求映射到 auto_assign 方法
})


urlpatterns = [
    # 注册 API
    path('register/', RegisterView.as_view(), name='register'),

    # 登录 API
    path('login/', LoginView.as_view(), name='login'),

    path('token/refresh/', refresh_admin_token, name='admin_token_refresh'),

    path('profile/', AdminProfileView.as_view(), name='admin-profile'),

    # simple-jwt 提供的用于刷新 access token 的接口
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),

    # 批量注册 API
    path('register/bulk/', BulkRegisterView.as_view(), name='bulk-register'),

    # 下载模板 API
    path('register/template/', DownloadTemplateView.as_view(), name='download-template'),


    path('teachers/register/bulk/', BulkRegisterTeachersView.as_view(), name='teacher-bulk-register'),

    path('teachers/register/template/', DownloadTeacherTemplateView.as_view(), name='teacher-download-template'),

    path('students/register/bulk/', BulkRegisterStudentsView.as_view(), name='student-bulk-register'),

    path('students/register/template/', DownloadStudentTemplateView.as_view(), name='student-download-template'),

    path('mutualselectionevents/', mutual_selection_list, name='mutual-selection-event-list'),
    # 学生管理的 ViewSet 路由
    path('', include(router.urls)),
    path('majors/', MajorListView.as_view(), name='major-list'),

    path('mutualselectionevents/', mutual_selection_list, name='mutual-selection-event-list'),
    # 详情、更新和删除
    path('mutualselectionevents/<int:pk>/', mutual_selection_detail, name='mutual-selection-event-detail'),
    # 批量删除
    path('mutualselectionevents/bulk-delete/', mutual_selection_bulk_delete, name='mutual-selection-event-bulk-delete'),
    path('mutualselectionevents/<int:pk>/auto-assign/', mutual_selection_auto_assign,name='mutual-selection-event-auto-assign'),
]
