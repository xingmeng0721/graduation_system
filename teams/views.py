from rest_framework import generics, status, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.views import APIView
from django.db.models import Q
from django.utils import timezone
from django.db import transaction
from .models import Team, TeamMembership, TeamInvitation
from .serializers import (
    TeamSerializer, TeamCreateSerializer, TeamListSerializer,
    TeamMembershipSerializer, TeamMembershipCreateSerializer, TeamMembershipUpdateSerializer,
    TeamInvitationSerializer, TeamInvitationCreateSerializer
)


class TeamListCreateView(generics.ListCreateAPIView):
    """团队列表和创建视图"""
    
    def get_serializer_class(self):
        if self.request.method == 'POST':
            return TeamCreateSerializer
        return TeamListSerializer
    
    def get_queryset(self):
        queryset = Team.objects.all().select_related('leader')
        
        # 筛选条件
        status_filter = self.request.query_params.get('status')
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        
        is_public = self.request.query_params.get('is_public')
        if is_public == 'true':
            queryset = queryset.filter(is_public=True)
        
        # 搜索
        search = self.request.query_params.get('search')
        if search:
            queryset = queryset.filter(
                Q(name__icontains=search) |
                Q(project_title__icontains=search) |
                Q(description__icontains=search)
            )
        
        return queryset.order_by('-created_at')
    
    def get_permissions(self):
        if self.request.method == 'POST':
            return [permissions.IsAuthenticated()]
        return [permissions.AllowAny()]
    
    def create(self, request, *args, **kwargs):
        # 检查用户是否为学生
        if not request.user.is_student:
            return Response(
                {'error': '只有学生可以创建团队'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # 检查用户是否已经是某个团队的成员
        if TeamMembership.objects.filter(student=request.user, status='approved').exists():
            return Response(
                {'error': '您已经是某个团队的成员'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        return super().create(request, *args, **kwargs)


class TeamDetailView(generics.RetrieveUpdateDestroyAPIView):
    """团队详情视图"""
    queryset = Team.objects.all()
    serializer_class = TeamSerializer
    
    def get_permissions(self):
        # 查看详情所有人可以，修改删除需要是队长
        if self.request.method in ['PUT', 'PATCH', 'DELETE']:
            return [permissions.IsAuthenticated()]
        return [permissions.AllowAny()]
    
    def update(self, request, *args, **kwargs):
        team = self.get_object()
        if not team.is_leader(request.user):
            return Response(
                {'error': '只有队长可以修改团队信息'},
                status=status.HTTP_403_FORBIDDEN
            )
        return super().update(request, *args, **kwargs)
    
    def destroy(self, request, *args, **kwargs):
        team = self.get_object()
        if not team.is_leader(request.user):
            return Response(
                {'error': '只有队长可以解散团队'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # 将团队状态设为已解散，而不是删除
        team.status = 'disbanded'
        team.save()
        
        return Response({'message': '团队已解散'}, status=status.HTTP_204_NO_CONTENT)


class MyTeamsView(generics.ListAPIView):
    """我的团队视图"""
    serializer_class = TeamListSerializer
    
    def get_queryset(self):
        return Team.objects.filter(
            memberships__student=self.request.user,
            memberships__status='approved'
        ).distinct().order_by('-created_at')


class TeamMembershipListCreateView(generics.ListCreateAPIView):
    """团队成员申请列表和创建视图"""
    
    def get_serializer_class(self):
        if self.request.method == 'POST':
            return TeamMembershipCreateSerializer
        return TeamMembershipSerializer
    
    def get_queryset(self):
        team_id = self.kwargs.get('team_id')
        return TeamMembership.objects.filter(team_id=team_id).select_related('student', 'team')
    
    def create(self, request, *args, **kwargs):
        # 检查用户是否为学生
        if not request.user.is_student:
            return Response(
                {'error': '只有学生可以申请加入团队'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # 检查用户是否已经是某个团队的成员
        if TeamMembership.objects.filter(student=request.user, status='approved').exists():
            return Response(
                {'error': '您已经是某个团队的成员'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        return super().create(request, *args, **kwargs)


class TeamMembershipDetailView(generics.RetrieveUpdateAPIView):
    """团队成员申请详情视图"""
    queryset = TeamMembership.objects.all()
    serializer_class = TeamMembershipUpdateSerializer
    
    def update(self, request, *args, **kwargs):
        membership = self.get_object()
        
        # 只有队长可以处理申请
        if not membership.team.is_leader(request.user):
            return Response(
                {'error': '只有队长可以处理成员申请'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # 检查团队是否还能接受成员
        if (request.data.get('status') == 'approved' and 
            not membership.team.can_add_members):
            return Response(
                {'error': '团队已满员'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # 设置处理时间
        if request.data.get('status') in ['approved', 'rejected']:
            membership.processed_at = timezone.now()
            membership.save()
        
        return super().update(request, *args, **kwargs)


class TeamInvitationListCreateView(generics.ListCreateAPIView):
    """团队邀请列表和创建视图"""
    
    def get_serializer_class(self):
        if self.request.method == 'POST':
            return TeamInvitationCreateSerializer
        return TeamInvitationSerializer
    
    def get_queryset(self):
        # 显示用户收到的邀请
        return TeamInvitation.objects.filter(
            invitee=self.request.user
        ).select_related('team', 'inviter', 'invitee').order_by('-created_at')


class MyInvitationsView(generics.ListAPIView):
    """我的邀请视图"""
    serializer_class = TeamInvitationSerializer
    
    def get_queryset(self):
        # 区分收到的和发出的邀请
        invitation_type = self.request.query_params.get('type', 'received')
        
        if invitation_type == 'sent':
            return TeamInvitation.objects.filter(
                inviter=self.request.user
            ).select_related('team', 'inviter', 'invitee').order_by('-created_at')
        else:
            return TeamInvitation.objects.filter(
                invitee=self.request.user
            ).select_related('team', 'inviter', 'invitee').order_by('-created_at')


class TeamInvitationDetailView(generics.RetrieveUpdateAPIView):
    """团队邀请详情视图"""
    queryset = TeamInvitation.objects.all()
    serializer_class = TeamInvitationSerializer
    
    def update(self, request, *args, **kwargs):
        invitation = self.get_object()
        
        # 只有被邀请人可以回应邀请
        if invitation.invitee != request.user:
            return Response(
                {'error': '只有被邀请人可以回应邀请'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # 检查邀请是否已过期
        if invitation.is_expired:
            return Response(
                {'error': '邀请已过期'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        new_status = request.data.get('status')
        if new_status not in ['accepted', 'declined']:
            return Response(
                {'error': '状态必须是 accepted 或 declined'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        with transaction.atomic():
            invitation.status = new_status
            invitation.responded_at = timezone.now()
            invitation.save()
            
            # 如果接受邀请，创建团队成员资格
            if new_status == 'accepted':
                # 检查用户是否已经是团队成员
                if not invitation.team.is_member(request.user):
                    # 检查团队是否还能接受成员
                    if invitation.team.can_add_members:
                        TeamMembership.objects.create(
                            team=invitation.team,
                            student=request.user,
                            status='approved',
                            applied_at=timezone.now(),
                            processed_at=timezone.now()
                        )
                    else:
                        return Response(
                            {'error': '团队已满员'},
                            status=status.HTTP_400_BAD_REQUEST
                        )
        
        return Response({
            'message': f'邀请已{"接受" if new_status == "accepted" else "拒绝"}',
            'invitation': TeamInvitationSerializer(invitation).data
        })


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def leave_team_view(request, team_id):
    """离开团队"""
    try:
        team = Team.objects.get(id=team_id)
        membership = TeamMembership.objects.get(team=team, student=request.user, status='approved')
        
        # 队长不能直接离开，需要先转让队长或解散团队
        if team.is_leader(request.user):
            return Response(
                {'error': '队长不能直接离开团队，请先转让队长职位或解散团队'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        membership.status = 'left'
        membership.save()
        
        return Response({'message': '已离开团队'})
        
    except Team.DoesNotExist:
        return Response({'error': '团队不存在'}, status=status.HTTP_404_NOT_FOUND)
    except TeamMembership.DoesNotExist:
        return Response({'error': '您不是该团队成员'}, status=status.HTTP_400_BAD_REQUEST)
