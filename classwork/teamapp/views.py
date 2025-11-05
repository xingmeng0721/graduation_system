from django.utils import timezone
from django.db import transaction
from django.db.models import Case, When, Value, IntegerField, OuterRef, Subquery
from rest_framework import status, viewsets, serializers
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from adminapp.models import MutualSelectionEvent
from studentapp.models import Student
from teacherapp.models import teacher
from .models import Group, GroupMembership, TeacherGroupPreference
from .serializers import (
    GroupDetailSerializer,
    GroupCreateUpdateSerializer,
    TeamAdvisorSerializer,
    AvailableTeammateSerializer,
    TeacherPreferenceSerializer,
)


class TeamViewSet(viewsets.GenericViewSet):
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        if self.action == 'available_teammates':
            return Student.objects.none()
        return Group.objects.all()

    def get_serializer_class(self):
        if self.action in ['create_team', 'update_my_team']:
            return GroupCreateUpdateSerializer
        if self.action == 'available_teachers':
            return TeamAdvisorSerializer
        if self.action == 'available_teammates':
            return AvailableTeammateSerializer
        # [新增] 为教师设置志愿的 action 指定序列化器
        if self.action == 'set_preferences_by_teacher':
            return TeacherPreferenceSerializer
        return GroupDetailSerializer

    # --- 辅助函数 (get_active_event_for_student 保持不变) ---
    def get_active_event_for_student(self, student: Student):
        now = timezone.now()
        return MutualSelectionEvent.objects.filter(students=student, stu_start_time__lte=now,
                                                   stu_end_time__gte=now).first()

    def get_active_event_for_teacher(self, current_teacher: teacher):
        now = timezone.now()
        return MutualSelectionEvent.objects.filter(teachers=current_teacher, tea_start_time__lte=now,
                                                   tea_end_time__gte=now).first()

    @action(detail=False, methods=['get'], url_path='dashboard')
    def dashboard(self, request):
        student = request.user
        if not isinstance(student, Student): return Response({'error': '当前用户不是学生账号'},
                                                             status=status.HTTP_403_FORBIDDEN)
        active_event = self.get_active_event_for_student(student)
        response_data = {'has_active_event': active_event is not None, 'active_event_info': None, 'my_team_info': None,
                         'is_captain': False}
        if active_event: response_data['active_event_info'] = {'event_id': active_event.event_id,
                                                               'event_name': active_event.event_name,
                                                               'end_time': active_event.stu_end_time}
        try:
            membership = student.membership
            group = membership.group
            response_data['my_team_info'] = GroupDetailSerializer(group).data
            response_data['is_captain'] = (group.captain == student)
        except GroupMembership.DoesNotExist:
            pass
        return Response(response_data)

    @action(detail=False, methods=['get'], url_path='student/history')
    def student_history(self, request):
        current_student = request.user
        if not isinstance(current_student, Student):
            return Response({'error': '当前用户不是学生账号'}, status=status.HTTP_403_FORBIDDEN)

        now = timezone.now()
        past_events = MutualSelectionEvent.objects.filter(
            students=current_student,
            stu_end_time__lt=now,
            tea_end_time__lt=now
        ).order_by('-stu_end_time')

        data = [{'event_id': e.event_id, 'event_name': e.event_name, 'end_time': e.stu_end_time} for e in past_events]
        return Response(data)

    @action(detail=True, methods=['get'], url_path='student/history-detail')
    def student_history_detail(self, request, pk=None):
        current_student = request.user
        if not isinstance(current_student, Student):
            return Response({'error': '当前用户不是学生账号'}, status=status.HTTP_403_FORBIDDEN)

        try:
            event = MutualSelectionEvent.objects.get(pk=pk, students=current_student)
        except MutualSelectionEvent.DoesNotExist:
            return Response({'error': '活动不存在或您未参与该活动'}, status=status.HTTP_404_NOT_FOUND)

        # 查找该学生在该活动中的团队
        group = Group.objects.filter(event=event, members=current_student).first()

        response_data = {
            'event_name': event.event_name,
            'my_team_info': GroupDetailSerializer(group).data if group else None,
        }
        return Response(response_data)

    @action(detail=False, methods=['post'], url_path='create-team')
    @transaction.atomic
    def create_team(self, request):
        student = request.user
        if hasattr(student, 'membership'): return Response({'error': '您已在一个团队中，不能创建新团队'},
                                                           status=status.HTTP_400_BAD_REQUEST)
        active_event = self.get_active_event_for_student(student)
        if not active_event: return Response({'error': '您没有参与正在进行的互选活动，无法创建团队'},
                                             status=status.HTTP_400_BAD_REQUEST)
        serializer = self.get_serializer(data=request.data, context={'active_event': active_event})
        serializer.is_valid(raise_exception=True)
        group = serializer.save(event=active_event, captain=student)
        GroupMembership.objects.create(student=student, group=group)
        return Response(GroupDetailSerializer(group).data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['post'], url_path='join')
    @transaction.atomic
    def join_team(self, request, pk=None):
        student = request.user
        if hasattr(student, 'membership'): return Response({'error': '您已在一个团队中，请先退出'},
                                                           status=status.HTTP_400_BAD_REQUEST)
        active_event = self.get_active_event_for_student(student)
        if not active_event: return Response({'error': '您没有参与正在进行的互选活动'},
                                             status=status.HTTP_400_BAD_REQUEST)
        try:
            group = self.get_queryset().get(pk=pk, event=active_event)
        except Group.DoesNotExist:
            return Response({'error': '该团队不存在或不属于当前活动'}, status=status.HTTP_404_NOT_FOUND)
        GroupMembership.objects.create(student=student, group=group)
        return Response({'message': '成功加入团队'}, status=status.HTTP_200_OK)

    @action(detail=False, methods=['post'], url_path='leave-team')
    @transaction.atomic
    def leave_team(self, request):
        student = request.user
        try:
            membership = student.membership
            group = membership.group
            if group.captain == student:
                if group.members.count() > 1:
                    return Response({'error': '您是队长，请先将队长转让给其他成员或解散团队后再退出'},
                                    status=status.HTTP_400_BAD_REQUEST)
                else:
                    group.delete()
                    return Response({'message': '您是团队唯一的成员，退出后团队已解散'}, status=status.HTTP_200_OK)
            else:
                membership.delete()
                return Response({'message': '您已成功退出团队'}, status=status.HTTP_200_OK)
        except GroupMembership.DoesNotExist:
            return Response({'error': '您当前不属于任何团队'}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['get'], url_path='all-teams')
    def all_teams_in_active_event(self, request):
        student = request.user
        active_event = self.get_active_event_for_student(student)
        if not active_event: return Response([], status=status.HTTP_200_OK)
        queryset = self.get_queryset().filter(event=active_event).select_related('captain', 'advisor').prefetch_related(
            'members')
        return Response(GroupDetailSerializer(queryset, many=True).data)

    @action(detail=False, methods=['put'], url_path='my-team/update')
    def update_my_team(self, request):
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
        if not student_id_to_remove: return Response({'error': '必须提供要移除的成员ID (student_id)'},
                                                     status=status.HTTP_400_BAD_REQUEST)
        try:
            if captain.pk == int(student_id_to_remove): return Response({'error': '您不能移除自己'},
                                                                        status=status.HTTP_400_BAD_REQUEST)
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
        try:
            group = request.user.led_group
            group.delete()
            return Response({'message': '团队已成功解散'}, status=status.HTTP_200_OK)
        except Group.DoesNotExist:
            return Response({'error': '您不是队长'}, status=status.HTTP_403_FORBIDDEN)

    @action(detail=False, methods=['get'], url_path='available-teachers')
    def available_teachers(self, request):
        student = request.user
        active_event = self.get_active_event_for_student(student)
        if not active_event: return Response({'error': '您没有参与正在进行的互选活动'},
                                             status=status.HTTP_400_BAD_REQUEST)
        return Response(self.get_serializer(active_event.teachers.all(), many=True).data)

    @action(detail=False, methods=['get'], url_path='available-teammates')
    def available_teammates(self, request):
        student = request.user
        active_event = self.get_active_event_for_student(student)
        if not active_event: return Response({'error': '您没有参与正在进行的互选活动'},
                                             status=status.HTTP_400_BAD_REQUEST)
        grouped_student_ids = GroupMembership.objects.filter(group__event=active_event).values_list('student_id',
                                                                                                    flat=True)
        available_students = active_event.students.exclude(pk__in=grouped_student_ids).exclude(pk=student.pk)
        return Response(self.get_serializer(available_students, many=True).data)

    @action(detail=False, methods=['post'], url_path='my-team/add-member')
    @transaction.atomic
    def add_member(self, request):
        captain = request.user
        try:
            group = captain.led_group
        except Group.DoesNotExist:
            return Response({'error': '您不是任何团队的队长，无法执行此操作'}, status=status.HTTP_403_FORBIDDEN)
        student_id = request.data.get('student_id')
        if not student_id: return Response({'error': '必须提供学生ID'}, status=status.HTTP_400_BAD_REQUEST)
        try:
            student_to_add = Student.objects.get(pk=student_id)
        except Student.DoesNotExist:
            return Response({'error': '该学生不存在'}, status=status.HTTP_404_NOT_FOUND)
        if hasattr(student_to_add, 'membership'): return Response(
            {'error': f'无法添加，因为 {student_to_add.stu_name} 已加入其他团队。'}, status=status.HTTP_400_BAD_REQUEST)
        active_event = self.get_active_event_for_student(captain)
        if not active_event or not active_event.students.filter(pk=student_to_add.pk).exists(): return Response(
            {'error': f'无法添加，因为 {student_to_add.stu_name} 未参与当前活动。'}, status=status.HTTP_400_BAD_REQUEST)
        GroupMembership.objects.create(student=student_to_add, group=group)
        return Response({'message': f'已成功将 {student_to_add.stu_name} 加入团队'}, status=status.HTTP_200_OK)

    # --- 教师端 API (全新重构) ---

    @action(detail=False, methods=['get'], url_path='teacher/dashboard')
    def teacher_dashboard(self, request):
        """
        [全新] 教师端仪表盘，提供活动信息、可选小组列表和已选志愿。
        """
        current_teacher = request.user
        if not isinstance(current_teacher, teacher):
            return Response({'error': '当前用户不是教师账号'}, status=status.HTTP_403_FORBIDDEN)

        active_event = self.get_active_event_for_teacher(current_teacher)
        if not active_event:
            return Response({"teams": [], "preferences": {}, "active_event": None}, status=status.HTTP_200_OK)

        # 获取当前活动下的所有小组
        teams_in_event = Group.objects.filter(event=active_event).prefetch_related('members', 'captain')

        # 获取当前老师的志愿选择
        preferences = TeacherGroupPreference.objects.filter(teacher=current_teacher, group__event=active_event)
        preferences_data = {str(p.preference_rank): p.group_id for p in preferences}

        # 为每个小组标注是否已被当前老师选为志愿
        my_preference_subquery = TeacherGroupPreference.objects.filter(
            teacher=current_teacher,
            group=OuterRef('pk')
        ).values('preference_rank')[:1]

        queryset = teams_in_event.annotate(
            my_preference_rank=Subquery(my_preference_subquery, output_field=IntegerField())
        )

        serializer = GroupDetailSerializer(queryset, many=True)
        teams_data = serializer.data
        for i, group_obj in enumerate(queryset):
            teams_data[i]['my_preference_rank'] = group_obj.my_preference_rank

        return Response({
            "teams": teams_data,
            "preferences": preferences_data,
            "active_event": {
                "event_id": active_event.event_id,
                "event_name": active_event.event_name,
                "end_time": active_event.tea_end_time,
                "teacher_choice_limit": active_event.teacher_choice_limit,  # 传递上限给前端
            }
        })

    @action(detail=False, methods=['post'], url_path='teacher/set-preferences')
    @transaction.atomic
    def set_preferences_by_teacher(self, request):
        """
        [全新] 教师设置自己的志愿小组。
        """
        current_teacher = request.user
        if not isinstance(current_teacher, teacher):
            return Response({'error': '当前用户不是教师账号'}, status=status.HTTP_403_FORBIDDEN)

        active_event = self.get_active_event_for_teacher(current_teacher)
        if not active_event:
            return Response({'error': '当前没有正在进行的互选活动'}, status=status.HTTP_400_BAD_REQUEST)

        # 传入限制数进行验证
        context = {'limit': active_event.teacher_choice_limit}
        serializer = self.get_serializer(data=request.data, context=context)
        serializer.is_valid(raise_exception=True)

        preferences_dict = serializer.validated_data.get('preferences')

        # 1. 先清除该老师在此活动中的所有旧志愿
        TeacherGroupPreference.objects.filter(teacher=current_teacher, group__event=active_event).delete()

        # 2. 创建新的志愿对象
        new_preferences = []
        for rank, group_id in preferences_dict.items():
            new_preferences.append(
                TeacherGroupPreference(
                    teacher=current_teacher,
                    group_id=group_id,
                    preference_rank=int(rank)
                )
            )

        # 3. 批量创建新志愿
        if new_preferences:
            TeacherGroupPreference.objects.bulk_create(new_preferences)

        return Response({'message': '志愿设置成功！'}, status=status.HTTP_200_OK)

    @action(detail=False, methods=['get'], url_path='teacher/history')
    def history(self, request):
        current_teacher = request.user
        if not isinstance(current_teacher, teacher):
            return Response({'error': '当前用户不是教师账号'}, status=status.HTTP_403_FORBIDDEN)

        now = timezone.now()
        # 筛选出当前老师参与过，并且两个结束时间都已经过去的活动
        past_events = MutualSelectionEvent.objects.filter(
            teachers=current_teacher,
            stu_end_time__lt=now,
            tea_end_time__lt=now
        ).order_by('-tea_end_time')

        # 使用一个简单的序列化器返回列表
        data = [{'event_id': e.event_id, 'event_name': e.event_name, 'end_time': e.tea_end_time} for e in past_events]
        return Response(data)

    # [新增] 获取单个已结束活动的详细结果
    @action(detail=True, methods=['get'], url_path='teacher/history-detail')
    def history_detail(self, request, pk=None):
        current_teacher = request.user
        if not isinstance(current_teacher, teacher):
            return Response({'error': '当前用户不是教师账号'}, status=status.HTTP_403_FORBIDDEN)

        try:
            # 确保活动存在且老师参与过
            event = MutualSelectionEvent.objects.get(pk=pk, teachers=current_teacher)
        except MutualSelectionEvent.DoesNotExist:
            return Response({'error': '活动不存在或您未参与该活动'}, status=status.HTTP_404_NOT_FOUND)

        # 查找该老师在该活动中最终指导的小组
        advised_groups = Group.objects.filter(event=event, advisor=current_teacher).prefetch_related('members',
                                                                                                     'captain')

        # 查找老师在该活动中提交的志愿
        preferences = TeacherGroupPreference.objects.filter(teacher=current_teacher, group__event=event)
        preferences_data = {str(p.preference_rank): p.group_id for p in preferences}

        response_data = {
            'event_name': event.event_name,
            'advised_groups': GroupDetailSerializer(advised_groups, many=True).data,
            'preferences': preferences_data,
            'all_teams_in_event': GroupDetailSerializer(event.groups.all(), many=True).data  # 提供所有小组信息用于前端匹配
        }
        return Response(response_data)

    # --- 自动分配占位符 (保持不变) ---
    @action(detail=True, methods=['post'], url_path='auto-assign')
    def auto_assign(self, request, *args, **kwargs):
        event = self.get_object()
        now = timezone.now()
        if event.stu_end_time > now or event.tea_end_time > now:
            return Response({'error': '该活动尚未对所有参与者结束，不能进行自动分配。'}, status=400)
        return Response({
            'message': '自动分配功能尚未实现，但接口已通。',
            'assigned_count': 0,
            'unassigned_count': len(event.students.all()),
            'unassigned_students': [{'stu_name': s.stu_name} for s in event.students.all()],
        }, status=200)