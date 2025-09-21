from django.urls import path
from . import views

urlpatterns = [
    # 团队相关
    path('', views.TeamListCreateView.as_view(), name='team-list-create'),
    path('<int:pk>/', views.TeamDetailView.as_view(), name='team-detail'),
    path('my-teams/', views.MyTeamsView.as_view(), name='my-teams'),
    path('<int:team_id>/leave/', views.leave_team_view, name='leave-team'),
    
    # 团队成员申请
    path('<int:team_id>/memberships/', views.TeamMembershipListCreateView.as_view(), name='team-membership-list-create'),
    path('memberships/<int:pk>/', views.TeamMembershipDetailView.as_view(), name='team-membership-detail'),
    
    # 团队邀请
    path('invitations/', views.TeamInvitationListCreateView.as_view(), name='team-invitation-list-create'),
    path('invitations/<int:pk>/', views.TeamInvitationDetailView.as_view(), name='team-invitation-detail'),
    path('my-invitations/', views.MyInvitationsView.as_view(), name='my-invitations'),
]