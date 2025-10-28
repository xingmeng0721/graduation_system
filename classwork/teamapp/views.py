from django.utils import timezone
from django.db import transaction
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from adminapp.models import MutualSelectionEvent
from studentapp.models import Student
from teacherapp.models import teacher
from .models import Group, GroupMembership
from .serializers import (
    GroupDetailSerializer,
    GroupCreateSerializer,
    TeamAdvisorSerializer
)


class TeamViewSet(viewsets.GenericViewSet):
    """
    学生团队管理视图集
    支持：创建团队、加入团队、退出团队、查看我的团队、查看当前活动
    """
    permission_classes = [IsAuthenticated]
    serializer_class = GroupDetailSerializer

    def get_queryset(self):
        return Group.objects.all()

    # ========== 工具函数 ==========
    def get_active_event(self, student: Student):
        """
        获取当前学生参与且正在进行的互选活动
        """
        now = timezone.now()
        return MutualSelectionEvent.objects.filter(
            students=student,
            start_time__lte=now,
            end_time__gte=now
        ).first()

    # ========== 视图方法 ==========
    @action(detail=False, methods=['get'], url_path='active-event')
    def get_active_event_for_student(self, request):
        """获取当前学生参与的、正在进行的互选活动"""
        student = request.user
        if not isinstance(student, Student):
            return Response({'error': '当前账号不是学生账号'}, status=status.HTTP_400_BAD_REQUEST)

        active_event = self.get_active_event(student)
        if active_event:
            return Response({
                'event_id': active_event.event_id,
                'event_name': active_event.event_name,
                'end_time': active_event.end_time
            })
        else:
            return Response({'detail': '当前没有正在进行的活动'}, status=status.HTTP_404_NOT_FOUND)

    @action(detail=False, methods=['get'], url_path='my-team')
    def my_team(self, request):
        """查看当前学生所在的团队"""
        student = request.user
        try:
            membership = student.membership
            group = membership.group
            serializer = self.get_serializer(group)
            return Response(serializer.data)
        except GroupMembership.DoesNotExist:
            return Response({'detail': '您尚未加入任何团队'}, status=status.HTTP_404_NOT_FOUND)

    @action(detail=False, methods=['post'], url_path='create-team')
    @transaction.atomic
    def create_team(self, request):
        """创建一个新团队，并将自己设为队长"""
        student = request.user
        if hasattr(student, 'membership'):
            return Response({'error': '您已在一个团队中，不能创建新团队'}, status=status.HTTP_400_BAD_REQUEST)

        active_event = self.get_active_event(student)
        if not active_event:
            return Response({'error': '您没有参与正在进行的互选活动，无法创建团队'}, status=status.HTTP_400_BAD_REQUEST)

        serializer = GroupCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        group = serializer.save(
            event=active_event,
            captain=student
        )
        # 队长自动加入团队
        GroupMembership.objects.create(student=student, group=group)

        return Response(self.get_serializer(group).data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['post'], url_path='join')
    @transaction.atomic
    def join_team(self, request, pk=None):
        """加入一个已存在的团队"""
        student = request.user
        if hasattr(student, 'membership'):
            return Response({'error': '您已在一个团队中，请先退出'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            group = self.get_object()
        except Group.DoesNotExist:
            return Response({'error': '团队不存在'}, status=status.HTTP_404_NOT_FOUND)

        active_event = self.get_active_event(student)
        if not active_event:
            return Response({'error': '您当前没有正在进行的互选活动'}, status=status.HTTP_400_BAD_REQUEST)

        if group.event_id != active_event.event_id:
            return Response({'error': '您不能加入不属于当前活动的团队'}, status=status.HTTP_400_BAD_REQUEST)

        # 验证该学生是否属于该活动的学生列表
        if not active_event.students.filter(pk=student.pk).exists():
            return Response({'error': '您未参与该活动，无法加入团队'}, status=status.HTTP_400_BAD_REQUEST)

        GroupMembership.objects.create(student=student, group=group)
        return Response({'message': '成功加入团队'}, status=status.HTTP_200_OK)

    @action(detail=False, methods=['post'], url_path='leave-team')
    @transaction.atomic
    def leave_team(self, request):
        """退出当前团队"""
        student = request.user
        try:
            membership = student.membership
            group = membership.group

            if group.captain == student:
                group.delete()
                return Response({'message': '您是队长，退出后团队已解散'}, status=status.HTTP_200_OK)
            else:
                membership.delete()
                return Response({'message': '您已成功退出团队'}, status=status.HTTP_200_OK)
        except GroupMembership.DoesNotExist:
            return Response({'error': '您当前不属于任何团队'}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['get'], url_path='available-teachers')
    def available_teachers(self, request):
        """获取当前活动的所有可选教师"""
        student = request.user
        active_event = self.get_active_event(student)
        if not active_event:
            return Response({'error': '您没有参与正在进行的互选活动'}, status=status.HTTP_400_BAD_REQUEST)

        teachers = active_event.teachers.all()
        serializer = TeamAdvisorSerializer(teachers, many=True)
        return Response(serializer.data)
