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
from .models import Group, GroupMembership, TeacherGroupPreference, ProvisionalAssignment
from .serializers import (
    GroupDetailSerializer,
    GroupCreateUpdateSerializer,
    TeamAdvisorSerializer,
    AvailableTeammateSerializer,
    TeacherPreferenceSerializer,
    ProvisionalAssignmentSerializer,

)
from adminapp.models import AdminUser

import random
from collections import defaultdict


def is_admin(user):
    return isinstance(user, AdminUser)


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
        if self.action == 'set_preferences_by_teacher':
            return TeacherPreferenceSerializer
        return GroupDetailSerializer

    # --- 辅助函数 ---
    def get_active_event_for_student(self, student: Student):
        now = timezone.now()
        return MutualSelectionEvent.objects.filter(
            students=student,
            stu_start_time__lte=now,
            stu_end_time__gte=now
        ).first()

    def get_active_event_for_teacher(self, current_teacher: teacher):
        now = timezone.now()
        return MutualSelectionEvent.objects.filter(
            teachers=current_teacher,
            tea_start_time__lte=now,
            tea_end_time__gte=now
        ).first()

    def get_student_membership_in_event(self, student: Student, event: MutualSelectionEvent):
        """获取学生在指定活动中的团队成员关系"""
        try:
            return GroupMembership.objects.get(student=student, group__event=event)
        except GroupMembership.DoesNotExist:
            return None

    def get_student_captained_group_in_event(self, student: Student, event: MutualSelectionEvent):
        """获取学生在指定活动中担任队长的团队"""
        try:
            return Group.objects.get(captain=student, event=event)
        except Group.DoesNotExist:
            return None

    # --- 学生端 API ---

    @action(detail=False, methods=['get'], url_path='dashboard')
    def dashboard(self, request):
        # ✅ 修正：直接使用 student，不使用 captain
        student = request.user
        if not isinstance(student, Student):
            return Response(
                {'error': '当前用户不是学生账号'},
                status=status.HTTP_403_FORBIDDEN
            )

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

            membership = self.get_student_membership_in_event(student, active_event)
            if membership:
                group = membership.group
                response_data['my_team_info'] = GroupDetailSerializer(group).data
                response_data['is_captain'] = (group.captain == student)

        return Response(response_data)

    @action(detail=False, methods=['get'], url_path='student/history')
    def student_history(self, request):
        student = request.user
        if not isinstance(student, Student):
            return Response(
                {'error': '当前用户不是学生账号'},
                status=status.HTTP_403_FORBIDDEN
            )

        now = timezone.now()
        past_events = MutualSelectionEvent.objects.filter(
            students=student,
            stu_end_time__lt=now,
            tea_end_time__lt=now
        ).order_by('-stu_end_time')

        data = [
            {
                'event_id': e.event_id,
                'event_name': e.event_name,
                'end_time': e.stu_end_time
            }
            for e in past_events
        ]
        return Response(data)

    @action(detail=True, methods=['get'], url_path='student/history-detail')
    def student_history_detail(self, request, pk=None):
        student = request.user
        if not isinstance(student, Student):
            return Response(
                {'error': '当前用户不是学生账号'},
                status=status.HTTP_403_FORBIDDEN
            )

        try:
            event = MutualSelectionEvent.objects.get(pk=pk, students=student)
        except MutualSelectionEvent.DoesNotExist:
            return Response(
                {'error': '活动不存在或您未参与该活动'},
                status=status.HTTP_404_NOT_FOUND
            )

        group = Group.objects.filter(event=event, members=student).first()

        response_data = {
            'event_name': event.event_name,
            'my_team_info': GroupDetailSerializer(group).data if group else None,
        }
        return Response(response_data)

    @action(detail=False, methods=['post'], url_path='create-team')
    @transaction.atomic
    def create_team(self, request):
        # ✅ 修正：使用 student
        student = request.user
        if not isinstance(student, Student):
            return Response(
                {'error': '当前用户不是学生账号'},
                status=status.HTTP_403_FORBIDDEN
            )

        active_event = self.get_active_event_for_student(student)
        if not active_event:
            return Response(
                {'error': '您没有参与正在进行的互选活动，无法创建团队'},
                status=status.HTTP_400_BAD_REQUEST
            )

        if self.get_student_membership_in_event(student, active_event):
            return Response(
                {'error': '您已在本次活动的一个团队中，不能创建新团队'},
                status=status.HTTP_400_BAD_REQUEST
            )

        serializer = self.get_serializer(
            data=request.data,
            context={'active_event': active_event}
        )
        serializer.is_valid(raise_exception=True)

        # ✅ 修正：captain 参数使用 student
        group = serializer.save(event=active_event, captain=student)
        GroupMembership.objects.create(student=student, group=group)

        return Response(
            GroupDetailSerializer(group).data,
            status=status.HTTP_201_CREATED
        )

    @action(detail=True, methods=['post'], url_path='join')
    @transaction.atomic
    def join_team(self, request, pk=None):
        student = request.user
        if not isinstance(student, Student):
            return Response(
                {'error': '当前用户不是学生账号'},
                status=status.HTTP_403_FORBIDDEN
            )

        active_event = self.get_active_event_for_student(student)
        if not active_event:
            return Response(
                {'error': '您没有参与正在进行的互选活动'},
                status=status.HTTP_400_BAD_REQUEST
            )

        if self.get_student_membership_in_event(student, active_event):
            return Response(
                {'error': '您已在本次活动的一个团队中，请先退出'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            group = self.get_queryset().get(pk=pk, event=active_event)
        except Group.DoesNotExist:
            return Response(
                {'error': '该团队不存在或不属于当前活动'},
                status=status.HTTP_404_NOT_FOUND
            )

        GroupMembership.objects.create(student=student, group=group)
        return Response({'message': '成功加入团队'}, status=status.HTTP_200_OK)

    @action(detail=False, methods=['post'], url_path='leave-team')
    @transaction.atomic
    def leave_team(self, request):
        student = request.user
        if not isinstance(student, Student):
            return Response(
                {'error': '当前用户不是学生账号'},
                status=status.HTTP_403_FORBIDDEN
            )

        active_event = self.get_active_event_for_student(student)
        if not active_event:
            return Response(
                {'error': '当前没有进行中的活动'},
                status=status.HTTP_400_BAD_REQUEST
            )

        membership = self.get_student_membership_in_event(student, active_event)
        if not membership:
            return Response(
                {'error': '您当前不属于任何团队'},
                status=status.HTTP_400_BAD_REQUEST
            )

        group = membership.group
        if group.captain == student:
            if group.members.count() > 1:
                return Response({
                    'error': '您是队长，请先将队长转让给其他成员或解散团队后再退出'
                }, status=status.HTTP_400_BAD_REQUEST)
            else:
                group.delete()
                return Response(
                    {'message': '您是团队唯一的成员,退出后团队已解散'},
                    status=status.HTTP_200_OK
                )
        else:
            membership.delete()
            return Response(
                {'message': '您已成功退出团队'},
                status=status.HTTP_200_OK
            )

    @action(detail=False, methods=['get'], url_path='all-teams')
    def all_teams_in_active_event(self, request):
        student = request.user
        if not isinstance(student, Student):
            return Response(
                {'error': '当前用户不是学生账号'},
                status=status.HTTP_403_FORBIDDEN
            )

        active_event = self.get_active_event_for_student(student)
        if not active_event:
            return Response([], status=status.HTTP_200_OK)

        queryset = self.get_queryset().filter(event=active_event).select_related(
            'captain', 'advisor'
        ).prefetch_related('members')

        return Response(GroupDetailSerializer(queryset, many=True).data)

    @action(detail=False, methods=['put'], url_path='my-team/update')
    def update_my_team(self, request):
        # ✅ 修正：变量命名统一使用 student
        student = request.user
        if not isinstance(student, Student):
            return Response(
                {'error': '当前用户不是学生账号'},
                status=status.HTTP_403_FORBIDDEN
            )

        active_event = self.get_active_event_for_student(student)
        if not active_event:
            return Response(
                {'error': '当前没有进行中的活动'},
                status=status.HTTP_400_BAD_REQUEST
            )

        group = self.get_student_captained_group_in_event(student, active_event)
        if not group:
            return Response(
                {'error': '您不是本次活动中任何团队的队长'},
                status=status.HTTP_403_FORBIDDEN
            )

        serializer = self.get_serializer(
            group,
            data=request.data,
            partial=True,
            context={'active_event': active_event}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response(GroupDetailSerializer(group).data)

    @action(detail=False, methods=['post'], url_path='my-team/remove-member')
    @transaction.atomic
    def remove_member(self, request):
        # ✅ 修正：统一使用 student
        student = request.user
        if not isinstance(student, Student):
            return Response(
                {'error': '当前用户不是学生账号'},
                status=status.HTTP_403_FORBIDDEN
            )

        active_event = self.get_active_event_for_student(student)
        if not active_event:
            return Response(
                {'error': '当前没有进行中的活动'},
                status=status.HTTP_400_BAD_REQUEST
            )

        group = self.get_student_captained_group_in_event(student, active_event)
        if not group:
            return Response(
                {'error': '您不是本次活动中任何团队的队长，无法执行此操作'},
                status=status.HTTP_403_FORBIDDEN
            )

        student_id_to_remove = request.data.get('student_id')
        if not student_id_to_remove:
            return Response(
                {'error': '必须提供要移除的成员ID (student_id)'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            if student.pk == int(student_id_to_remove):
                return Response(
                    {'error': '您不能移除自己'},
                    status=status.HTTP_400_BAD_REQUEST
                )
        except (ValueError, TypeError):
            return Response(
                {'error': '无效的成员ID格式'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            membership_to_delete = GroupMembership.objects.get(
                student_id=student_id_to_remove,
                group=group
            )
            student_name = membership_to_delete.student.stu_name
            membership_to_delete.delete()
            return Response(
                {'message': f'已成功将成员 {student_name} 移出团队'},
                status=status.HTTP_200_OK
            )
        except GroupMembership.DoesNotExist:
            return Response(
                {'error': '该成员不存在或不属于您的团队'},
                status=status.HTTP_404_NOT_FOUND
            )

    @action(detail=False, methods=['post'], url_path='my-team/disband')
    def disband_team(self, request):
        student = request.user
        if not isinstance(student, Student):
            return Response(
                {'error': '当前用户不是学生账号'},
                status=status.HTTP_403_FORBIDDEN
            )

        active_event = self.get_active_event_for_student(student)
        if not active_event:
            return Response(
                {'error': '当前没有进行中的活动'},
                status=status.HTTP_400_BAD_REQUEST
            )

        group = self.get_student_captained_group_in_event(student, active_event)
        if not group:
            return Response(
                {'error': '您不是本次活动中任何团队的队长'},
                status=status.HTTP_403_FORBIDDEN
            )

        group.delete()
        return Response({'message': '团队已成功解散'}, status=status.HTTP_200_OK)

    @action(detail=False, methods=['get'], url_path='available-teachers')
    def available_teachers(self, request):
        student = request.user
        if not isinstance(student, Student):
            return Response(
                {'error': '当前用户不是学生账号'},
                status=status.HTTP_403_FORBIDDEN
            )

        active_event = self.get_active_event_for_student(student)
        if not active_event:
            return Response(
                {'error': '您没有参与正在进行的互选活动'},
                status=status.HTTP_400_BAD_REQUEST
            )

        return Response(
            self.get_serializer(active_event.teachers.all(), many=True).data
        )

    @action(detail=False, methods=['get'], url_path='available-teammates')
    def available_teammates(self, request):
        student = request.user
        if not isinstance(student, Student):
            return Response(
                {'error': '当前用户不是学生账号'},
                status=status.HTTP_403_FORBIDDEN
            )

        active_event = self.get_active_event_for_student(student)
        if not active_event:
            return Response(
                {'error': '您没有参与正在进行的互选活动'},
                status=status.HTTP_400_BAD_REQUEST
            )

        grouped_student_ids = GroupMembership.objects.filter(
            group__event=active_event
        ).values_list('student_id', flat=True)

        available_students = active_event.students.exclude(
            pk__in=grouped_student_ids
        ).exclude(pk=student.pk)

        return Response(
            self.get_serializer(available_students, many=True).data
        )

    @action(detail=False, methods=['post'], url_path='my-team/add-member')
    @transaction.atomic
    def add_member(self, request):
        # ✅ 修正：统一使用 student
        student = request.user
        if not isinstance(student, Student):
            return Response(
                {'error': '当前用户不是学生账号'},
                status=status.HTTP_403_FORBIDDEN
            )

        active_event = self.get_active_event_for_student(student)
        if not active_event:
            return Response(
                {'error': '当前没有进行中的活动'},
                status=status.HTTP_400_BAD_REQUEST
            )

        group = self.get_student_captained_group_in_event(student, active_event)
        if not group:
            return Response(
                {'error': '您不是本次活动中任何团队的队长，无法执行此操作'},
                status=status.HTTP_403_FORBIDDEN
            )

        student_id = request.data.get('student_id')
        if not student_id:
            return Response(
                {'error': '必须提供学生ID'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            student_to_add = Student.objects.get(pk=student_id)
        except Student.DoesNotExist:
            return Response(
                {'error': '该学生不存在'},
                status=status.HTTP_404_NOT_FOUND
            )

        if self.get_student_membership_in_event(student_to_add, active_event):
            return Response({
                'error': f'无法添加，因为 {student_to_add.stu_name} 已加入本次活动的其他团队。'
            }, status=status.HTTP_400_BAD_REQUEST)

        if not active_event.students.filter(pk=student_to_add.pk).exists():
            return Response({
                'error': f'无法添加，因为 {student_to_add.stu_name} 未参与当前活动。'
            }, status=status.HTTP_400_BAD_REQUEST)

        GroupMembership.objects.create(student=student_to_add, group=group)
        return Response(
            {'message': f'已成功将 {student_to_add.stu_name} 加入团队'},
            status=status.HTTP_200_OK
        )

    @action(detail=True, methods=['get'], url_path='group-detail')
    def get_group_detail(self, request, pk=None):
        """
        获取团队的完整详细信息
        学生可以查看任何团队的详细信息（包括成员联系方式）
        """
        student = request.user
        if not isinstance(student, Student):
            return Response(
                {'error': '当前用户不是学生账号'},
                status=status.HTTP_403_FORBIDDEN
            )

        try:
            group = Group.objects.prefetch_related(
                'members__major',
                'captain',
                'advisor',
                'preferred_advisor_1',
                'preferred_advisor_2',
                'preferred_advisor_3'
            ).get(pk=pk)
        except Group.DoesNotExist:
            return Response(
                {'error': '团队不存在'},
                status=status.HTTP_404_NOT_FOUND
            )

        # 检查学生是否有权查看（参与了该活动）
        active_event = self.get_active_event_for_student(student)
        if active_event and group.event == active_event:
            # 当前活动中的团队，可以查看
            return Response(GroupDetailSerializer(group).data)

        # 检查是否是历史活动中的团队
        if group.event.students.filter(pk=student.pk).exists():
            return Response(GroupDetailSerializer(group).data)

        return Response(
            {'error': '您没有权限查看该团队信息'},
            status=status.HTTP_403_FORBIDDEN
        )

    # --- 教师端 API ---

    @action(detail=False, methods=['get'], url_path='teacher/dashboard')
    def teacher_dashboard(self, request):
        current_teacher = request.user
        if not isinstance(current_teacher, teacher):
            return Response(
                {'error': '当前用户不是教师账号'},
                status=status.HTTP_403_FORBIDDEN
            )

        active_event = self.get_active_event_for_teacher(current_teacher)
        if not active_event:
            return Response({
                "teams": [],
                "preferences": {},
                "active_event": None
            }, status=status.HTTP_200_OK)

        teams_in_event = Group.objects.filter(event=active_event).prefetch_related(
            'members', 'captain'
        )

        preferences = TeacherGroupPreference.objects.filter(
            teacher=current_teacher,
            group__event=active_event
        )
        preferences_data = {str(p.preference_rank): p.group_id for p in preferences}

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
                "teacher_choice_limit": active_event.teacher_choice_limit,
            }
        })

    @action(detail=False, methods=['post'], url_path='teacher/set-preferences')
    @transaction.atomic
    def set_preferences_by_teacher(self, request):
        current_teacher = request.user
        if not isinstance(current_teacher, teacher):
            return Response(
                {'error': '当前用户不是教师账号'},
                status=status.HTTP_403_FORBIDDEN
            )

        active_event = self.get_active_event_for_teacher(current_teacher)
        if not active_event:
            return Response(
                {'error': '当前没有正在进行的互选活动'},
                status=status.HTTP_400_BAD_REQUEST
            )

        context = {
            'active_event': active_event,
            'limit': active_event.teacher_choice_limit
        }
        serializer = self.get_serializer(data=request.data, context=context)
        serializer.is_valid(raise_exception=True)

        preferences_dict = serializer.validated_data.get('preferences')

        TeacherGroupPreference.objects.filter(
            teacher=current_teacher,
            group__event=active_event
        ).delete()

        new_preferences = []
        for rank, group_id in preferences_dict.items():
            new_preferences.append(
                TeacherGroupPreference(
                    teacher=current_teacher,
                    group_id=group_id,
                    preference_rank=int(rank)
                )
            )

        if new_preferences:
            TeacherGroupPreference.objects.bulk_create(new_preferences)

        return Response({'message': '志愿设置成功！'}, status=status.HTTP_200_OK)

    @action(detail=False, methods=['get'], url_path='teacher/history')
    def history(self, request):
        current_teacher = request.user
        if not isinstance(current_teacher, teacher):
            return Response(
                {'error': '当前用户不是教师账号'},
                status=status.HTTP_403_FORBIDDEN
            )

        now = timezone.now()
        past_events = MutualSelectionEvent.objects.filter(
            teachers=current_teacher,
            stu_end_time__lt=now,
            tea_end_time__lt=now
        ).order_by('-tea_end_time')

        data = [
            {
                'event_id': e.event_id,
                'event_name': e.event_name,
                'end_time': e.tea_end_time
            }
            for e in past_events
        ]
        return Response(data)

    @action(detail=True, methods=['get'], url_path='teacher/history-detail')
    def history_detail(self, request, pk=None):
        current_teacher = request.user
        if not isinstance(current_teacher, teacher):
            return Response(
                {'error': '当前用户不是教师账号'},
                status=status.HTTP_403_FORBIDDEN
            )

        try:
            event = MutualSelectionEvent.objects.get(pk=pk, teachers=current_teacher)
        except MutualSelectionEvent.DoesNotExist:
            return Response(
                {'error': '活动不存在或您未参与该活动'},
                status=status.HTTP_404_NOT_FOUND
            )

        advised_groups = Group.objects.filter(
            event=event,
            advisor=current_teacher
        ).prefetch_related('members', 'captain')

        preferences = TeacherGroupPreference.objects.filter(
            teacher=current_teacher,
            group__event=event
        )
        preferences_data = {str(p.preference_rank): p.group_id for p in preferences}

        response_data = {
            'event_name': event.event_name,
            'advised_groups': GroupDetailSerializer(advised_groups, many=True).data,
            'preferences': preferences_data,
            'all_teams_in_event': GroupDetailSerializer(event.groups.all(), many=True).data
        }
        return Response(response_data)

    @action(detail=True, methods=['get'], url_path='teacher/group-detail')
    def teacher_get_group_detail(self, request, pk=None):
        """
        教师查看团队的完整详细信息
        包括所有成员的联系方式和详细信息
        """
        current_teacher = request.user
        if not isinstance(current_teacher, teacher):
            return Response(
                {'error': '当前用户不是教师账号'},
                status=status.HTTP_403_FORBIDDEN
            )

        try:
            group = Group.objects.prefetch_related(
                'members__major',
                'captain',
                'advisor'
            ).get(pk=pk)
        except Group.DoesNotExist:
            return Response(
                {'error': '团队不存在'},
                status=status.HTTP_404_NOT_FOUND
            )

        # 检查教师是否有权查看（参与了该活动）
        if not group.event.teachers.filter(teacher_id=current_teacher.teacher_id).exists():
            return Response(
                {'error': '您没有权限查看该团队信息'},
                status=status.HTTP_403_FORBIDDEN
            )

        return Response(GroupDetailSerializer(group).data)

    @action(detail=False, methods=['get'], url_path='teacher/current-advised-groups')
    def get_current_advised_groups(self, request):
        """
       获取教师在当前活动中指导的团队
        """
        current_teacher = request.user
        if not isinstance(current_teacher, teacher):
            return Response(
                {'error': '当前用户不是教师账号'},
                status=status.HTTP_403_FORBIDDEN
            )

        active_event = self.get_active_event_for_teacher(current_teacher)
        if not active_event:
            return Response({
                'message': '当前没有正在进行的活动',
                'groups': []
            })

        # 获取当前活动中指导的团队
        advised_groups = Group.objects.filter(
            event=active_event,
            advisor=current_teacher
        ).prefetch_related(
            'members__major',
            'captain'
        )

        return Response({
            'event_id': active_event.event_id,
            'event_name': active_event.event_name,
            'groups': GroupDetailSerializer(advised_groups, many=True).data})

    # --- 管理员端 API ---

    @action(detail=True, methods=['post'], url_path='admin/auto-assign')
    @transaction.atomic
    def auto_assign(self, request, pk=None):
        if not is_admin(request.user):
            return Response({'error': '无权访问'}, status=status.HTTP_403_FORBIDDEN)

        try:
            event = MutualSelectionEvent.objects.get(pk=pk)
        except MutualSelectionEvent.DoesNotExist:
            return Response({'error': '活动不存在'}, status=status.HTTP_404_NOT_FOUND)

        now = timezone.now()
        if not (event.stu_end_time < now and event.tea_end_time < now):
            return Response(
                {'error': '活动尚未对所有参与者结束，不能进行分配。'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # 清除旧的临时分配
        ProvisionalAssignment.objects.filter(event=event).delete()

        groups = list(Group.objects.filter(event=event))
        teachers = list(event.teachers.all())

        if not groups:
            return Response({'error': '当前活动没有任何团队'}, status=status.HTTP_400_BAD_REQUEST)

        if not teachers:
            return Response({'error': '当前活动没有参与的教师'}, status=status.HTTP_400_BAD_REQUEST)

        # 构建学生志愿字典
        student_prefs = {
            g.group_id: [
                g.preferred_advisor_1_id,
                g.preferred_advisor_2_id,
                g.preferred_advisor_3_id
            ]
            for g in groups
        }

        # 构建教师志愿字典
        teacher_prefs = {
            t.teacher_id: {
                pref.group_id: pref.preference_rank
                for pref in t.group_preferences.filter(group__event=event)
            }
            for t in teachers
        }

        # 教师剩余容量
        teacher_capacity = {t.teacher_id: event.teacher_choice_limit for t in teachers}

        # 权重和评分规则
        TEACHER_WEIGHT_MULTIPLIER = 1.2  # 教师志愿权重稍高
        TEACHER_PREF_SCORES = {1: 10, 2: 8, 3: 6, 4: 4, 5: 2}
        STUDENT_PREF_SCORES = {1: 10, 2: 5, 3: 2}

        # ========== 第一阶段：基于双向志愿的优先匹配 ==========
        scores = []
        for group in groups:
            for t in teachers:
                teacher_score = 0
                student_score = 0
                explanation_parts = []

                # 计算教师志愿得分
                teacher_rank = teacher_prefs.get(t.teacher_id, {}).get(group.group_id)
                if teacher_rank:
                    teacher_score = TEACHER_PREF_SCORES.get(teacher_rank, 0)
                    if teacher_score > 0:
                        explanation_parts.append(f"教师第{teacher_rank}志愿")

                # 计算学生志愿得分
                try:
                    student_rank = student_prefs[group.group_id].index(t.teacher_id) + 1
                    student_score = STUDENT_PREF_SCORES.get(student_rank, 0)
                    if student_score > 0:
                        explanation_parts.append(f"学生第{student_rank}志愿")
                except (ValueError, IndexError):
                    pass

                # 计算总分
                total_score = (teacher_score * TEACHER_WEIGHT_MULTIPLIER) + student_score

                # 即使总分为0也要记录，用于后续随机分配
                scores.append({
                    'group': group,
                    'teacher': t,
                    'score': round(total_score, 2),
                    'explanation': " + ".join(explanation_parts) if explanation_parts else "无志愿匹配",
                    'has_preference': total_score > 0
                })

        # 按得分降序排序
        scores.sort(key=lambda x: (x['has_preference'], x['score']), reverse=True)

        assigned_groups = set()
        provisional_assignments = []

        # ========== 第二阶段：优先匹配有志愿的组合 ==========
        for match in scores:
            if not match['has_preference']:
                break  # 已经到无志愿匹配的部分了

            group, teacher_obj = match['group'], match['teacher']
            if group.group_id in assigned_groups or teacher_capacity[teacher_obj.teacher_id] <= 0:
                continue

            provisional_assignments.append(
                ProvisionalAssignment(
                    event=event,
                    group=group,
                    teacher=teacher_obj,
                    assignment_type='auto',
                    score=match['score'],
                    explanation=match['explanation']
                )
            )
            assigned_groups.add(group.group_id)
            teacher_capacity[teacher_obj.teacher_id] -= 1

        # ========== 第三阶段：随机分配剩余团队 ==========
        unassigned_groups = [g for g in groups if g.group_id not in assigned_groups]
        available_teachers_list = [t for t in teachers if teacher_capacity[t.teacher_id] > 0]

        if unassigned_groups and available_teachers_list:
            # 打乱教师顺序，实现随机性
            random.shuffle(available_teachers_list)

            for group in unassigned_groups:
                # 找到还有容量的教师
                assigned = False
                for t in available_teachers_list:
                    if teacher_capacity[t.teacher_id] > 0:
                        provisional_assignments.append(
                            ProvisionalAssignment(
                                event=event,
                                group=group,
                                teacher=t,
                                assignment_type='auto',
                                score=0.0,
                                explanation='随机分配（无志愿匹配）'
                            )
                        )
                        assigned_groups.add(group.group_id)
                        teacher_capacity[t.teacher_id] -= 1
                        assigned = True
                        break

                # 如果所有教师都满额，但还有未分配的团队，需要扩容
                if not assigned:
                    # 找到当前指导团队最少的教师
                    min_assigned_teacher = min(teachers,
                                               key=lambda t: event.teacher_choice_limit - teacher_capacity[
                                                   t.teacher_id])

                    provisional_assignments.append(
                        ProvisionalAssignment(
                            event=event,
                            group=group,
                            teacher=min_assigned_teacher,
                            assignment_type='auto',
                            score=0.0,
                            explanation=f'超额分配（原名额已满）'
                        )
                    )
                    assigned_groups.add(group.group_id)
                    # 注意：这里不再减少容量，因为已经超额了

        # 批量创建分配记录
        ProvisionalAssignment.objects.bulk_create(provisional_assignments)

        # 统计信息
        preference_matched = sum(1 for pa in provisional_assignments if pa.score > 0)
        random_assigned = sum(1 for pa in provisional_assignments if pa.score == 0)
        over_capacity_teachers = [
            t.teacher_name for t in teachers
            if teacher_capacity[t.teacher_id] < 0
        ]

        return Response({
            'message': '自动分配完成！',
            'total_groups': len(groups),
            'total_teachers': len(teachers),
            'assigned_count': len(provisional_assignments),
            'preference_matched': preference_matched,
            'random_assigned': random_assigned,
            'unassigned_count': len(groups) - len(provisional_assignments),
            'over_capacity_teachers': over_capacity_teachers,
            'details': f'志愿匹配: {preference_matched}组，随机分配: {random_assigned}组'
        })

    @action(detail=True, methods=['get'], url_path='admin/match-options')
    def get_match_options(self, request, pk=None):
        """
        ✅ 新增：获取指定团队的所有可能教师匹配选项及得分
        用于管理员手动分配时参考
        """
        if not is_admin(request.user):
            return Response({'error': '无权访问'}, status=status.HTTP_403_FORBIDDEN)

        group_id = request.query_params.get('group_id')
        if not group_id:
            return Response({'error': '缺少 group_id 参数'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            group = Group.objects.get(pk=group_id, event_id=pk)
            event = MutualSelectionEvent.objects.get(pk=pk)
        except (Group.DoesNotExist, MutualSelectionEvent.DoesNotExist):
            return Response({'error': '团队或活动不存在'}, status=status.HTTP_404_NOT_FOUND)

        # 获取团队的学生志愿
        student_prefs = [
            group.preferred_advisor_1_id,
            group.preferred_advisor_2_id,
            group.preferred_advisor_3_id
        ]

        # 获取所有参与教师
        teachers = event.teachers.all()

        # 计算当前每个教师已分配的团队数
        teacher_assignments = defaultdict(int)
        for assignment in ProvisionalAssignment.objects.filter(event=event):
            teacher_assignments[assignment.teacher_id] += 1

        # 评分规则
        TEACHER_WEIGHT_MULTIPLIER = 1.2
        TEACHER_PREF_SCORES = {1: 10, 2: 8, 3: 6, 4: 4, 5: 2}
        STUDENT_PREF_SCORES = {1: 10, 2: 5, 3: 2}

        match_options = []
        for t in teachers:
            teacher_score = 0
            student_score = 0
            details = []

            # 计算教师志愿得分
            teacher_pref = TeacherGroupPreference.objects.filter(
                teacher=t,
                group=group
            ).first()

            if teacher_pref:
                teacher_score = TEACHER_PREF_SCORES.get(teacher_pref.preference_rank, 0)
                if teacher_score > 0:
                    details.append({
                        'type': 'teacher_preference',
                        'rank': teacher_pref.preference_rank,
                        'score': teacher_score * TEACHER_WEIGHT_MULTIPLIER,
                        'description': f'教师第{teacher_pref.preference_rank}志愿'
                    })

            # 计算学生志愿得分
            try:
                student_rank = student_prefs.index(t.teacher_id) + 1
                student_score = STUDENT_PREF_SCORES.get(student_rank, 0)
                if student_score > 0:
                    details.append({
                        'type': 'student_preference',
                        'rank': student_rank,
                        'score': student_score,
                        'description': f'学生第{student_rank}志愿'
                    })
            except (ValueError, IndexError):
                pass

            # 计算总分
            total_score = (teacher_score * TEACHER_WEIGHT_MULTIPLIER) + student_score

            # 判断是否超额
            current_load = teacher_assignments[t.teacher_id]
            is_over_capacity = current_load >= event.teacher_choice_limit

            match_options.append({
                'teacher_id': t.teacher_id,
                'teacher_name': t.teacher_name,
                'teacher_no': t.teacher_no,
                'research_direction': t.research_direction,
                'total_score': round(total_score, 2),
                'score_details': details,
                'current_load': current_load,
                'capacity_limit': event.teacher_choice_limit,
                'is_over_capacity': is_over_capacity,
                'load_percentage': round((current_load / event.teacher_choice_limit) * 100,
                                         1) if event.teacher_choice_limit > 0 else 0,
                'recommendation': self._get_recommendation(total_score, is_over_capacity)
            })

        # 按总分降序排序
        match_options.sort(key=lambda x: x['total_score'], reverse=True)

        return Response({
            'group_id': group.group_id,
            'group_name': group.group_name,
            'match_options': match_options
        })

    def _get_recommendation(self, score, is_over_capacity):
        """生成推荐等级"""
        if is_over_capacity:
            return '⚠️ 超额'
        elif score >= 15:
            return '🌟 强烈推荐'
        elif score >= 10:
            return '👍 推荐'
        elif score >= 5:
            return '✓ 可选'
        elif score > 0:
            return '- 一般'
        else:
            return '❌ 无匹配'

    @action(detail=True, methods=['get'], url_path='admin/all-match-options')
    def get_all_match_options(self, request, pk=None):
        """
        ✅ 新增：获取活动中所有团队和教师的匹配矩阵
        用于管理员全局查看匹配情况
        """
        if not is_admin(request.user):
            return Response({'error': '无权访问'}, status=status.HTTP_403_FORBIDDEN)

        try:
            event = MutualSelectionEvent.objects.get(pk=pk)
        except MutualSelectionEvent.DoesNotExist:
            return Response({'error': '活动不存在'}, status=status.HTTP_404_NOT_FOUND)

        groups = Group.objects.filter(event=event)
        teachers = event.teachers.all()

        # 构建学生志愿字典
        student_prefs = {
            g.group_id: [
                g.preferred_advisor_1_id,
                g.preferred_advisor_2_id,
                g.preferred_advisor_3_id
            ]
            for g in groups
        }

        # 构建教师志愿字典
        teacher_prefs_map = {}
        for pref in TeacherGroupPreference.objects.filter(group__event=event):
            key = (pref.teacher_id, pref.group_id)
            teacher_prefs_map[key] = pref.preference_rank

        # 计算教师当前负载
        teacher_assignments = defaultdict(int)
        for assignment in ProvisionalAssignment.objects.filter(event=event):
            teacher_assignments[assignment.teacher_id] += 1

        # 评分规则
        TEACHER_WEIGHT_MULTIPLIER = 1.2
        TEACHER_PREF_SCORES = {1: 10, 2: 8, 3: 6, 4: 4, 5: 2}
        STUDENT_PREF_SCORES = {1: 10, 2: 5, 3: 2}

        # 构建匹配矩阵
        match_matrix = []
        for group in groups:
            group_matches = {
                'group_id': group.group_id,
                'group_name': group.group_name,
                'captain_name': group.captain.stu_name if group.captain else '无',
                'member_count': group.members.count(),
                'teachers': []
            }

            for t in teachers:
                teacher_score = 0
                student_score = 0

                # 教师志愿得分
                teacher_rank = teacher_prefs_map.get((t.teacher_id, group.group_id))
                if teacher_rank:
                    teacher_score = TEACHER_PREF_SCORES.get(teacher_rank, 0) * TEACHER_WEIGHT_MULTIPLIER

                # 学生志愿得分
                try:
                    student_rank = student_prefs[group.group_id].index(t.teacher_id) + 1
                    student_score = STUDENT_PREF_SCORES.get(student_rank, 0)
                except (ValueError, IndexError):
                    pass

                total_score = teacher_score + student_score
                current_load = teacher_assignments[t.teacher_id]
                is_over_capacity = current_load >= event.teacher_choice_limit

                group_matches['teachers'].append({
                    'teacher_id': t.teacher_id,
                    'teacher_name': t.teacher_name,
                    'score': round(total_score, 2),
                    'teacher_rank': teacher_rank,
                    'student_rank': student_prefs[group.group_id].index(t.teacher_id) + 1 if t.teacher_id in
                                                                                             student_prefs[
                                                                                                 group.group_id] else None,
                    'current_load': current_load,
                    'is_over_capacity': is_over_capacity
                })

            # 按得分排序
            group_matches['teachers'].sort(key=lambda x: x['score'], reverse=True)
            match_matrix.append(group_matches)

        # 教师统计
        teacher_stats = []
        for t in teachers:
            assigned_count = teacher_assignments[t.teacher_id]
            teacher_stats.append({
                'teacher_id': t.teacher_id,
                'teacher_name': t.teacher_name,
                'assigned_count': assigned_count,
                'capacity_limit': event.teacher_choice_limit,
                'remaining_capacity': max(0, event.teacher_choice_limit - assigned_count),
                'is_over_capacity': assigned_count > event.teacher_choice_limit
            })

        return Response({
            'event_name': event.event_name,
            'total_groups': groups.count(),
            'total_teachers': teachers.count(),
            'match_matrix': match_matrix,
            'teacher_stats': teacher_stats
        })

    @action(detail=True, methods=['get'], url_path='admin/get-assignments')
    def get_assignments(self, request, pk=None):
        if not is_admin(request.user):
            return Response({'error': '无权访问'}, status=status.HTTP_403_FORBIDDEN)

        assignments = ProvisionalAssignment.objects.filter(
            event_id=pk
        ).select_related(
            'group', 'teacher', 'group__captain'
        ).prefetch_related('group__members')

        serializer = ProvisionalAssignmentSerializer(assignments, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['post'], url_path='admin/manual-assign')
    @transaction.atomic
    def manual_assign(self, request, pk=None):
        if not is_admin(request.user):
            return Response({'error': '无权访问'}, status=status.HTTP_403_FORBIDDEN)

        event_id = pk
        group_id = request.data.get('group_id')
        teacher_id = request.data.get('teacher_id')

        try:
            event = MutualSelectionEvent.objects.get(pk=event_id)
            group = Group.objects.get(pk=group_id, event_id=event_id)
        except (MutualSelectionEvent.DoesNotExist, Group.DoesNotExist):
            return Response(
                {'error': '活动或小组不存在'},
                status=status.HTTP_404_NOT_FOUND
            )

        ProvisionalAssignment.objects.filter(group=group).delete()

        if teacher_id:
            try:
                teacher_obj = event.teachers.get(pk=teacher_id)
            except teacher.DoesNotExist:
                return Response(
                    {'error': '该教师未参与此活动'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            assigned_count = ProvisionalAssignment.objects.filter(
                event=event,
                teacher=teacher_obj
            ).count()
            if assigned_count >= event.teacher_choice_limit:
                return Response({
                    'error': f'操作失败，教师 {teacher_obj.teacher_name} 的指导名额已满。'
                }, status=status.HTTP_400_BAD_REQUEST)

            ProvisionalAssignment.objects.create(
                event=event,
                group=group,
                teacher=teacher_obj,
                assignment_type='manual',
                score=9999,
                explanation='管理员手动指定'
            )
            return Response({
                'message': f'已手动将小组"{group.group_name}"分配给 {teacher_obj.teacher_name}。'
            })

        return Response({'message': f'已取消小组"{group.group_name}"的分配。'})

    @action(detail=True, methods=['post'], url_path='admin/publish')
    @transaction.atomic
    def publish(self, request, pk=None):
        if not is_admin(request.user):
            return Response({'error': '无权访问'}, status=status.HTTP_403_FORBIDDEN)

        event_id = pk
        try:
            event = MutualSelectionEvent.objects.get(pk=event_id)
        except MutualSelectionEvent.DoesNotExist:
            return Response({'error': '活动不存在'}, status=status.HTTP_404_NOT_FOUND)

        Group.objects.filter(event=event).update(advisor=None)

        provisional_assignments = ProvisionalAssignment.objects.filter(event=event)
        if not provisional_assignments.exists():
            return Response(
                {'error': '没有可发布的分配结果'},
                status=status.HTTP_400_BAD_REQUEST
            )

        for pa in provisional_assignments:
            Group.objects.filter(pk=pa.group_id).update(advisor=pa.teacher)

        return Response({
            'message': f'结果发布成功！共为 {provisional_assignments.count()} 个团队确定了最终导师。'
        })