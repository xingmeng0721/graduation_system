from rest_framework import generics, status, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.views import APIView
from django.db.models import Q, Count
from django.utils import timezone
from django.contrib.auth import get_user_model
from .models import MentorSelection, TeacherSelection, SelectionPeriod
from teams.models import Team, TeamMembership
from accounts.models import TeacherProfile
from .serializers import (
    MentorSelectionSerializer, MentorSelectionCreateSerializer, MentorSelectionUpdateSerializer,
    TeacherSelectionSerializer, TeacherSelectionCreateSerializer,
    SelectionPeriodSerializer, MySelectionStatusSerializer, StatisticsSerializer
)

User = get_user_model()


class MentorSelectionListCreateView(generics.ListCreateAPIView):
    """导师选择列表和创建视图"""
    
    def get_serializer_class(self):
        if self.request.method == 'POST':
            return MentorSelectionCreateSerializer
        return MentorSelectionSerializer
    
    def get_queryset(self):
        user = self.request.user
        
        if user.is_student:
            # 学生看到自己的选择
            return MentorSelection.objects.filter(
                Q(student=user) | Q(team__leader=user)
            ).select_related('student', 'team', 'teacher').order_by('-applied_at')
        elif user.is_teacher:
            # 导师看到选择自己的申请
            return MentorSelection.objects.filter(
                teacher=user
            ).select_related('student', 'team', 'teacher').order_by('-applied_at')
        else:
            # 管理员看到所有
            return MentorSelection.objects.all().select_related(
                'student', 'team', 'teacher'
            ).order_by('-applied_at')
    
    def create(self, request, *args, **kwargs):
        # 检查用户是否为学生
        if not request.user.is_student:
            return Response(
                {'error': '只有学生可以选择导师'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        return super().create(request, *args, **kwargs)


class MentorSelectionDetailView(generics.RetrieveUpdateAPIView):
    """导师选择详情视图"""
    queryset = MentorSelection.objects.all()
    
    def get_serializer_class(self):
        if self.request.method in ['PUT', 'PATCH']:
            return MentorSelectionUpdateSerializer
        return MentorSelectionSerializer
    
    def update(self, request, *args, **kwargs):
        selection = self.get_object()
        
        # 只有导师可以更新状态
        if selection.teacher != request.user:
            return Response(
                {'error': '只有导师可以处理选择申请'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # 设置处理时间
        if request.data.get('status') in ['approved', 'rejected']:
            selection.processed_at = timezone.now()
            selection.save()
            
            # 如果通过，更新导师的当前学生数
            if request.data.get('status') == 'approved':
                teacher_profile, created = TeacherProfile.objects.get_or_create(
                    user=selection.teacher
                )
                if selection.selection_type == 'individual':
                    teacher_profile.current_students += 1
                else:  # team
                    # 团队算作团队成员数的学生
                    member_count = selection.team.current_member_count
                    teacher_profile.current_students += member_count
                teacher_profile.save()
        
        return super().update(request, *args, **kwargs)


class TeacherSelectionListCreateView(generics.ListCreateAPIView):
    """导师选择学生列表和创建视图"""
    
    def get_serializer_class(self):
        if self.request.method == 'POST':
            return TeacherSelectionCreateSerializer
        return TeacherSelectionSerializer
    
    def get_queryset(self):
        user = self.request.user
        
        if user.is_teacher:
            # 导师看到自己的选择
            return TeacherSelection.objects.filter(
                teacher=user
            ).select_related('teacher', 'student', 'team').order_by('-created_at')
        elif user.is_student:
            # 学生看到选择自己的导师
            return TeacherSelection.objects.filter(
                Q(student=user) | Q(team__memberships__student=user, team__memberships__status='approved')
            ).select_related('teacher', 'student', 'team').order_by('-created_at')
        else:
            # 管理员看到所有
            return TeacherSelection.objects.all().select_related(
                'teacher', 'student', 'team'
            ).order_by('-created_at')
    
    def create(self, request, *args, **kwargs):
        # 检查用户是否为导师
        if not request.user.is_teacher:
            return Response(
                {'error': '只有导师可以选择学生'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        return super().create(request, *args, **kwargs)


class TeacherSelectionDetailView(generics.RetrieveUpdateDestroyAPIView):
    """导师选择学生详情视图"""
    queryset = TeacherSelection.objects.all()
    serializer_class = TeacherSelectionSerializer
    
    def get_permissions(self):
        # 只有导师可以修改自己的选择
        return [permissions.IsAuthenticated()]
    
    def update(self, request, *args, **kwargs):
        selection = self.get_object()
        
        if selection.teacher != request.user:
            return Response(
                {'error': '只能修改自己的选择'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        return super().update(request, *args, **kwargs)
    
    def destroy(self, request, *args, **kwargs):
        selection = self.get_object()
        
        if selection.teacher != request.user:
            return Response(
                {'error': '只能删除自己的选择'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        return super().destroy(request, *args, **kwargs)


class SelectionPeriodListCreateView(generics.ListCreateAPIView):
    """选择周期列表和创建视图"""
    queryset = SelectionPeriod.objects.all()
    serializer_class = SelectionPeriodSerializer
    
    def get_permissions(self):
        # 只有管理员可以创建和修改选择周期
        if self.request.method == 'POST':
            return [permissions.IsAuthenticated()]  # 实际项目中应该是管理员权限
        return [permissions.AllowAny()]


class CurrentSelectionPeriodView(APIView):
    """当前活跃的选择周期"""
    permission_classes = [permissions.AllowAny]
    
    def get(self, request):
        try:
            period = SelectionPeriod.objects.filter(is_active=True).first()
            if period:
                serializer = SelectionPeriodSerializer(period)
                return Response(serializer.data)
            return Response({'message': '当前没有活跃的选择周期'}, status=status.HTTP_404_NOT_FOUND)
        except SelectionPeriod.DoesNotExist:
            return Response({'message': '当前没有活跃的选择周期'}, status=status.HTTP_404_NOT_FOUND)


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def my_selection_status_view(request):
    """我的选择状态"""
    user = request.user
    data = {
        'has_mentor': False,
        'mentor_selections': [],
        'received_teacher_selections': [],
        'team_mentor_selection': None
    }
    
    if user.is_student:
        # 个人导师选择
        mentor_selections = MentorSelection.objects.filter(student=user)
        data['mentor_selections'] = MentorSelectionSerializer(mentor_selections, many=True).data
        
        # 检查是否已有确认的导师
        data['has_mentor'] = mentor_selections.filter(status='approved').exists()
        
        # 收到的导师选择
        teacher_selections = TeacherSelection.objects.filter(student=user)
        data['received_teacher_selections'] = TeacherSelectionSerializer(teacher_selections, many=True).data
        
        # 团队导师选择（如果是队长）
        try:
            team = Team.objects.get(leader=user, status__in=['forming', 'complete'])
            team_selection = MentorSelection.objects.filter(team=team).first()
            if team_selection:
                data['team_mentor_selection'] = MentorSelectionSerializer(team_selection).data
                if team_selection.status == 'approved':
                    data['has_mentor'] = True
        except Team.DoesNotExist:
            pass
    
    elif user.is_teacher:
        # 导师收到的选择申请
        mentor_selections = MentorSelection.objects.filter(teacher=user)
        data['mentor_selections'] = MentorSelectionSerializer(mentor_selections, many=True).data
        
        # 导师主动的选择
        teacher_selections = TeacherSelection.objects.filter(teacher=user)
        data['received_teacher_selections'] = TeacherSelectionSerializer(teacher_selections, many=True).data
    
    return Response(data)


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def selection_statistics_view(request):
    """选择统计信息"""
    # 基础统计
    total_students = User.objects.filter(role='student').count()
    total_teachers = User.objects.filter(role='teacher').count()
    total_teams = Team.objects.filter(status__in=['forming', 'complete']).count()
    
    # 选择统计
    total_mentor_selections = MentorSelection.objects.count()
    pending_mentor_selections = MentorSelection.objects.filter(status='pending').count()
    approved_mentor_selections = MentorSelection.objects.filter(status='approved').count()
    
    # 有导师和无导师的学生数
    students_with_mentor = MentorSelection.objects.filter(
        status='approved'
    ).values('student', 'team').distinct().count()
    
    students_without_mentor = total_students - students_with_mentor
    
    # 如果是管理员或导师，提供更详细的统计
    detailed_stats = {}
    if request.user.is_admin_user or request.user.is_teacher:
        # 按院系统计
        dept_stats = User.objects.filter(role='student').values('department').annotate(
            count=Count('id')
        ).order_by('department')
        
        detailed_stats['department_stats'] = list(dept_stats)
        
        # 导师接收学生情况
        teacher_stats = []
        for teacher in User.objects.filter(role='teacher').select_related('teacher_profile'):
            profile = getattr(teacher, 'teacher_profile', None)
            teacher_stats.append({
                'teacher_name': teacher.real_name or teacher.username,
                'department': teacher.department,
                'max_students': profile.max_students if profile else 0,
                'current_students': profile.current_students if profile else 0,
                'is_accepting': profile.is_accepting if profile else True,
                'pending_selections': MentorSelection.objects.filter(
                    teacher=teacher, status='pending'
                ).count()
            })
        
        detailed_stats['teacher_stats'] = teacher_stats
    
    data = {
        'total_students': total_students,
        'total_teachers': total_teachers,
        'total_teams': total_teams,
        'total_mentor_selections': total_mentor_selections,
        'pending_mentor_selections': pending_mentor_selections,
        'approved_mentor_selections': approved_mentor_selections,
        'students_with_mentor': students_with_mentor,
        'students_without_mentor': students_without_mentor,
        **detailed_stats
    }
    
    return Response(data)
