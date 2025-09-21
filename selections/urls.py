from django.urls import path
from . import views

urlpatterns = [
    # 导师选择
    path('mentor-selections/', views.MentorSelectionListCreateView.as_view(), name='mentor-selection-list-create'),
    path('mentor-selections/<int:pk>/', views.MentorSelectionDetailView.as_view(), name='mentor-selection-detail'),
    
    # 导师选择学生
    path('teacher-selections/', views.TeacherSelectionListCreateView.as_view(), name='teacher-selection-list-create'),
    path('teacher-selections/<int:pk>/', views.TeacherSelectionDetailView.as_view(), name='teacher-selection-detail'),
    
    # 选择周期
    path('selection-periods/', views.SelectionPeriodListCreateView.as_view(), name='selection-period-list-create'),
    path('current-period/', views.CurrentSelectionPeriodView.as_view(), name='current-selection-period'),
    
    # 状态和统计
    path('my-status/', views.my_selection_status_view, name='my-selection-status'),
    path('statistics/', views.selection_statistics_view, name='selection-statistics'),
]