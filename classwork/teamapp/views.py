from django.utils import timezone
from django.db import transaction
from rest_framework import status, viewsets, serializers
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from adminapp.models import MutualSelectionEvent
from studentapp.models import Student
from teacherapp.models import teacher
from .models import Group, GroupMembership
from .serializers import (
    GroupDetailSerializer,
    GroupCreateUpdateSerializer,
    TeamAdvisorSerializer,
    AvailableTeammateSerializer
)


class TeamViewSet(viewsets.GenericViewSet):
    """
    学生团队管理视图集
    支持：创建/查看/更新/离开/解散团队，查看活动信息、可选导师和队友。
    """
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        # 根据不同的 action 返回不同的 queryset
        if self.action == 'available_teammates':
            # 在 available_teammates 中，我们会自己构建 queryset
            return Student.objects.none()
        return Group.objects.all()

    def get_serializer_class(self):
        # 根据 action 返回合适的序列化器
        if self.action in ['create_team', 'update_my_team']:
            return GroupCreateUpdateSerializer
        if self.action == 'available_teachers':
            return TeamAdvisorSerializer
        if self.action == 'available_teammates':
            return AvailableTeammateSerializer
        return GroupDetailSerializer

    # --- 辅助函数 ---
    def get_active_event_for_student(self, student: Student):
        """
        获取当前学生参与且正在进行的互选活动。
        **已修复**：使用 stu_start_time 和 stu_end_time。
        """
        now = timezone.now()
        return MutualSelectionEvent.objects.filter(
            students=student,
            stu_start_time__lte=now,
            stu_end_time__gte=now
        ).first()

    # --- 核心API端点 ---

    @action(detail=False, methods=['get'], url_path='dashboard')
    def dashboard(self, request):
        """
        提供给学生端的仪表盘信息，整合了多个常用查询。
        """
        student = request.user
        if not isinstance(student, Student):
            return Response({'error': '当前用户不是学生账号'}, status=status.HTTP_403_FORBIDDEN)

        active_event = self.get_active_event_for_student(student)

        response_data = {
            'has_active_event': active_event is not None,
            'active_event_info': None,
            'my_team_info': None,
            'is_captain': False
        }

        if active_event:
            response_data['active_event_info'] = {
                'event_id': active_event.event_id,
                'event_name': active_event.event_name,
                'end_time': active_event.stu_end_time
            }

        try:
            membership = student.membership
            group = membership.group
            response_data['my_team_info'] = GroupDetailSerializer(group).data
            response_data['is_captain'] = (group.captain == student)
        except GroupMembership.DoesNotExist:
            # 没有团队信息是正常情况
            pass

        return Response(response_data)

    @action(detail=False, methods=['post'], url_path='create-team')
    @transaction.atomic
    def create_team(self, request):
        """创建一个新团队，并将自己设为队长"""
        student = request.user
        if hasattr(student, 'membership'):
            return Response({'error': '您已在一个团队中，不能创建新团队'}, status=status.HTTP_400_BAD_REQUEST)

        active_event = self.get_active_event_for_student(student)
        if not active_event:
            return Response({'error': '您没有参与正在进行的互选活动，无法创建团队'}, status=status.HTTP_400_BAD_REQUEST)

        # 将 active_event 传入 serializer 的 context 中用于验证
        serializer = self.get_serializer(data=request.data, context={'active_event': active_event})
        serializer.is_valid(raise_exception=True)

        group = serializer.save(event=active_event, captain=student)
        GroupMembership.objects.create(student=student, group=group)

        return Response(GroupDetailSerializer(group).data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['post'], url_path='join')
    @transaction.atomic
    def join_team(self, request, pk=None):
        """加入一个已存在的团队"""
        student = request.user
        if hasattr(student, 'membership'):
            return Response({'error': '您已在一个团队中，请先退出'}, status=status.HTTP_400_BAD_REQUEST)

        active_event = self.get_active_event_for_student(student)
        if not active_event:
            return Response({'error': '您没有参与正在进行的互选活动'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            group = self.get_queryset().get(pk=pk, event=active_event)
        except Group.DoesNotExist:
            return Response({'error': '该团队不存在或不属于当前活动'}, status=status.HTTP_404_NOT_FOUND)

        GroupMembership.objects.create(student=student, group=group)
        return Response({'message': '成功加入团队'}, status=status.HTTP_200_OK)

    @action(detail=False, methods=['post'], url_path='leave-team')
    @transaction.atomic
    def leave_team(self, request):
        """退出当前团队。队长不能直接退出，必须先转让队长或解散团队。"""
        student = request.user
        try:
            membership = student.membership
            group = membership.group

            if group.captain == student:
                # 优化：队长不能直接退出，需要先处理团队
                if group.members.count() > 1:
                    return Response({'error': '您是队长，请先将队长转让给其他成员或解散团队后再退出'},
                                    status=status.HTTP_400_BAD_REQUEST)
                else:
                    # 如果团队只有队长一人，退出即解散
                    group.delete()
                    return Response({'message': '您是团队唯一的成员，退出后团队已解散'}, status=status.HTTP_200_OK)
            else:
                membership.delete()
                return Response({'message': '您已成功退出团队'}, status=status.HTTP_200_OK)
        except GroupMembership.DoesNotExist:
            return Response({'error': '您当前不属于任何团队'}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['get'], url_path='all-teams')
    def all_teams_in_active_event(self, request):
        """返回当前活动下的所有团队列表"""
        student = request.user
        active_event = self.get_active_event_for_student(student)
        if not active_event:
            return Response([], status=status.HTTP_200_OK)  # 如果没有活动，返回空列表

        queryset = self.get_queryset().filter(event=active_event).select_related(
            'captain', 'advisor'
        ).prefetch_related('members')
        serializer = GroupDetailSerializer(queryset, many=True)
        return Response(serializer.data)


    @action(detail=False, methods=['put'], url_path='my-team/update')
    def update_my_team(self, request):
        """队长更新团队信息（项目标题、描述、志愿导师）"""
        student = request.user
        try:
            group = student.led_group
        except Group.DoesNotExist:
            return Response({'error': '您不是任何团队的队长'}, status=status.HTTP_403_FORBIDDEN)

        active_event = self.get_active_event_for_student(student)
        serializer = self.get_serializer(group, data=request.data, partial=True, context={'active_event': active_event})
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(GroupDetailSerializer(group).data)

    @action(detail=False, methods=['post'], url_path='my-team/remove-member')
    @transaction.atomic
    def remove_member(self, request):
        captain = request.user
        try:
            group = captain.led_group
        except Group.DoesNotExist:
            return Response({'error': '您不是任何团队的队长，无法执行此操作'}, status=status.HTTP_403_FORBIDDEN)

        student_id_to_remove = request.data.get('student_id')
        if not student_id_to_remove:
            return Response({'error': '必须提供要移除的成员ID (student_id)'}, status=status.HTTP_400_BAD_REQUEST)

        # [修复] 确保在比较前进行类型转换
        try:
            if captain.pk == int(student_id_to_remove):
                return Response({'error': '您不能移除自己'}, status=status.HTTP_400_BAD_REQUEST)
        except (ValueError, TypeError):
            return Response({'error': '无效的成员ID格式'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            membership_to_delete = GroupMembership.objects.get(student_id=student_id_to_remove, group=group)
            student_name = membership_to_delete.student.stu_name
            membership_to_delete.delete()
            return Response({'message': f'已成功将成员 {student_name} 移出团队'}, status=status.HTTP_200_OK)
        except GroupMembership.DoesNotExist:
            return Response({'error': '该成员不存在或不属于您的团队'}, status=status.HTTP_404_NOT_FOUND)

    @action(detail=False, methods=['post'], url_path='my-team/disband')
    def disband_team(self, request):
        """队长解散团队"""
        try:
            group = request.user.led_group
            group.delete()
            return Response({'message': '团队已成功解散'}, status=status.HTTP_200_OK)
        except Group.DoesNotExist:
            return Response({'error': '您不是队长'}, status=status.HTTP_403_FORBIDDEN)


    @action(detail=False, methods=['get'], url_path='available-teachers')
    def available_teachers(self, request):
        """获取当前活动的所有可选教师"""
        student = request.user
        active_event = self.get_active_event_for_student(student)
        if not active_event:
            return Response({'error': '您没有参与正在进行的互选活动'}, status=status.HTTP_400_BAD_REQUEST)

        teachers = active_event.teachers.all()
        return Response(self.get_serializer(teachers, many=True).data)

    @action(detail=False, methods=['get'], url_path='available-teammates')
    def available_teammates(self, request):
        """获取当前活动中所有未组队的学生，作为可选的队友"""
        student = request.user
        active_event = self.get_active_event_for_student(student)
        if not active_event:
            return Response({'error': '您没有参与正在进行的互选活动'}, status=status.HTTP_400_BAD_REQUEST)

        # 找出所有已加入团队的学生ID
        grouped_student_ids = GroupMembership.objects.filter(group__event=active_event).values_list('student_id',
                                                                                                    flat=True)

        # 从当前活动的所有学生中，排除已组队的学生和自己
        available_students = active_event.students.exclude(pk__in=grouped_student_ids).exclude(pk=student.pk)

        return Response(self.get_serializer(available_students, many=True).data)

    @action(detail=False, methods=['post'], url_path='my-team/add-member')
    @transaction.atomic
    def add_member(self, request):
        """队长将一个未组队的学生直接添加到自己的团队中。"""
        captain = request.user
        try:
            # 确保操作者是队长
            group = captain.led_group
        except Group.DoesNotExist:
            return Response({'error': '您不是任何团队的队长，无法执行此操作'}, status=status.HTTP_403_FORBIDDEN)

        student_id = request.data.get('student_id')
        if not student_id:
            return Response({'error': '必须提供学生ID'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            student_to_add = Student.objects.get(pk=student_id)
        except Student.DoesNotExist:
            return Response({'error': '该学生不存在'}, status=status.HTTP_404_NOT_FOUND)

        # 检查学生是否已在团队中
        if hasattr(student_to_add, 'membership'):
            return Response({'error': f'无法添加，因为 {student_to_add.stu_name} 已加入其他团队。'},
                            status=status.HTTP_400_BAD_REQUEST)

        # 检查学生是否属于同一活动
        active_event = self.get_active_event_for_student(captain)
        if not active_event or not active_event.students.filter(pk=student_to_add.pk).exists():
            return Response({'error': f'无法添加，因为 {student_to_add.stu_name} 未参与当前活动。'},
                            status=status.HTTP_400_BAD_REQUEST)

        GroupMembership.objects.create(student=student_to_add, group=group)
        return Response({'message': f'已成功将 {student_to_add.stu_name} 加入团队'}, status=status.HTTP_200_OK)