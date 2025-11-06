from django.db.models import Count, Q
from django.utils import timezone
import django_filters
from django.contrib.auth import authenticate
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import generics, status, views, viewsets, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.parsers import MultiPartParser, FormParser
from django.contrib.auth.hashers import check_password, make_password
from .models import AdminUser, MutualSelectionEvent
from teacherapp.models import teacher
from .serializers import (
    AdminUserSerializer, LoginSerializer, UserProfileSerializer,
    StudentManagementSerializer, StudentListSerializer, MajorSerializer,
    TeacherManagementSerializer, TeacherProfileSerializer,
    MutualSelectionEventListSerializer, MutualSelectionEventSerializer
)
import pandas as pd
import io
from django.http import HttpResponse
from django.db import transaction

from rest_framework.permissions import IsAuthenticated, AllowAny
from studentapp.models import Student, Major
from teamapp.models import Group, GroupMembership


class RegisterView(generics.CreateAPIView):
    """
    管理员注册视图。
    使用 AdminUserSerializer，在创建用户时会自动加密密码。
    """
    queryset = AdminUser.objects.all()
    serializer_class = AdminUserSerializer


class LoginView(APIView):
    """
    管理员登录视图。手动实现用户验证和JWT生成。
    """
    permission_classes = [AllowAny]
    serializer_class = LoginSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)

        admin_username_val = serializer.validated_data.get('admin_username')
        password_val = serializer.validated_data.get('password')

        user = authenticate(request, admin_username=admin_username_val, password=password_val)

        if user and isinstance(user, AdminUser):
            refresh = RefreshToken()
            refresh['user_id'] = user.admin_id
            refresh['user_type'] = 'admin'

            return Response({
                'refresh': str(refresh),
                'access': str(refresh.access_token),
            }, status=status.HTTP_200_OK)
        else:
            return Response({'detail': '用户名或密码错误。'}, status=status.HTTP_401_UNAUTHORIZED)


class DownloadTemplateView(views.APIView):
    """
    下载用于批量注册的Excel模板
    """

    def get(self, request, *args, **kwargs):
        data = {
            'admin_name': ['示例用户', 'John Doe'],
            'admin_username': ['example_user', 'johndoe'],
            'password': ['password123', 'another_secret']
        }
        df = pd.DataFrame(data)

        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name='Users')

        output.seek(0)

        response = HttpResponse(
            output.read(),
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        response['Content-Disposition'] = 'attachment; filename="registration_template.xlsx"'

        return response


class BulkRegisterView(views.APIView):
    """
    通过导入Excel文件批量注册用户
    """
    parser_classes = (MultiPartParser, FormParser)

    @transaction.atomic
    def post(self, request, *args, **kwargs):
        file_obj = request.FILES.get('file')
        if not file_obj:
            return Response({'error': '未找到上传的文件。'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            df = pd.read_excel(file_obj)
        except Exception as e:
            return Response({'error': f'文件读取失败: {e}'}, status=status.HTTP_400_BAD_REQUEST)

        required_columns = {'admin_name', 'admin_username', 'password'}
        if not required_columns.issubset(df.columns):
            missing = required_columns - set(df.columns)
            return Response({'error': f'Excel文件中缺少必需的列: {", ".join(missing)}'},
                            status=status.HTTP_400_BAD_REQUEST)

        users_to_create = []

        for index, row in df.iterrows():
            admin_name = row.get('admin_name')
            admin_username = row.get('admin_username')
            password = row.get('password')

            if not all([admin_name, admin_username, password]):
                return Response({'error': f'行 {index + 2}: 所有字段均为必填项。'}, status=status.HTTP_400_BAD_REQUEST)

            if AdminUser.objects.filter(admin_username=admin_username).exists():
                return Response({'error': f'行 {index + 2}: 用户名 "{admin_username}" 已存在。'},
                                status=status.HTTP_400_BAD_REQUEST)
            if AdminUser.objects.filter(admin_name=admin_name).exists():
                return Response({'error': f'行 {index + 2}: 名称 "{admin_name}" 已存在。'},
                                status=status.HTTP_400_BAD_REQUEST)

            users_to_create.append(
                AdminUser(
                    admin_name=str(admin_name),
                    admin_username=str(admin_username),
                    admin_password=make_password(str(password))
                )
            )

        AdminUser.objects.bulk_create(users_to_create)

        return Response({'message': f'成功注册 {len(users_to_create)} 名用户。'}, status=status.HTTP_201_CREATED)


class DownloadTeacherTemplateView(views.APIView):
    """
    下载用于教师批量注册的Excel模板。
    """

    def get(self, request, *args, **kwargs):
        data = {
            'teacher_no': ['T2025001', 'T2025002'],
            'teacher_name': ['王老师', '李老师'],
            'password': ['initial_password1', 'initial_password2'],
            'phone': ['13900139000', ''],
            'email': ['wang@example.com', 'li@example.com'],
            'research_direction': ['计算机视觉', '自然语言处理'],
            'introduction': ['资深教授', '青年讲师']
        }
        df = pd.DataFrame(data)
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name='Teachers')
        output.seek(0)
        response = HttpResponse(
            output.read(),
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        response['Content-Disposition'] = 'attachment; filename="teacher_registration_template.xlsx"'
        return response


class BulkRegisterTeachersView(views.APIView):
    """
    通过上传Excel文件批量注册教师。
    """
    parser_classes = (MultiPartParser, FormParser)

    def post(self, request, *args, **kwargs):
        file_obj = request.FILES.get('file')
        if not file_obj:
            return Response({'error': '未找到上传的文件。'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            df = pd.read_excel(file_obj, dtype=str).fillna('')
        except Exception as e:
            return Response({'error': f'无法解析Excel文件: {e}'}, status=status.HTTP_400_BAD_REQUEST)

        required_columns = {'teacher_no', 'teacher_name', 'password'}
        if not required_columns.issubset(df.columns):
            missing = required_columns - set(df.columns)
            return Response({'error': f'Excel文件中缺少必需的列: {", ".join(missing)}'},
                            status=status.HTTP_400_BAD_REQUEST)

        teachers_to_create = []
        failed_entries = []
        existing_teacher_nos = set(teacher.objects.values_list('teacher_no', flat=True))

        for index, row in df.iterrows():
            row_num = index + 2
            teacher_no = row.get('teacher_no', '').strip()
            teacher_name = row.get('teacher_name', '').strip()
            password = row.get('password', '').strip()

            if not all([teacher_no, teacher_name, password]):
                failed_entries.append(
                    {'row': row_num, 'teacher_no': teacher_no, 'error': '缺少必填字段 (工号, 姓名, 密码)。'})
                continue

            if teacher_no in existing_teacher_nos:
                failed_entries.append(
                    {'row': row_num, 'teacher_no': teacher_no, 'error': f'工号 "{teacher_no}" 已存在。'})
                continue

            try:
                new_teacher = teacher(
                    teacher_no=teacher_no,
                    teacher_name=teacher_name,
                    phone=row.get('phone', '').strip() or None,
                    email=row.get('email', '').strip() or None,
                    research_direction=row.get('research_direction', '').strip() or None,
                    introduction=row.get('introduction', '').strip() or None,
                )
                new_teacher.set_password(password)
                teachers_to_create.append(new_teacher)
                existing_teacher_nos.add(teacher_no)
            except Exception as e:
                failed_entries.append(
                    {'row': row_num, 'teacher_no': teacher_no, 'error': f'创建教师对象时发生内部错误: {e}'})

        if teachers_to_create:
            with transaction.atomic():
                teacher.objects.bulk_create(teachers_to_create)

        return Response({
            'message': f'处理完成。成功注册 {len(teachers_to_create)} 名教师。',
            'success_count': len(teachers_to_create),
            'failure_count': len(failed_entries),
            'failed_entries': failed_entries
        }, status=status.HTTP_201_CREATED)


class DownloadStudentTemplateView(views.APIView):
    """
    下载用于学生批量注册的Excel模板。
    """

    def get(self, request, *args, **kwargs):
        data = {
            'stu_no': ['2024001', '2024002'],
            'stu_name': ['张三', '李四'],
            'password': ['initial_password1', 'initial_password2'],
            'grade': ['2024', '2024'],
            'major': ['计算机科学与技术', '软件工程'],
            'phone': ['13800138000', ''],
            'email': ['zhangsan@example.com', 'lisi@example.com']
        }
        df = pd.DataFrame(data)

        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name='Students')
        output.seek(0)

        response = HttpResponse(
            output.read(),
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        response['Content-Disposition'] = 'attachment; filename="student_registration_template.xlsx"'
        return response


class BulkRegisterStudentsView(views.APIView):
    """
    通过上传Excel文件批量注册学生。
    """
    parser_classes = (MultiPartParser, FormParser)

    def post(self, request, *args, **kwargs):
        file_obj = request.FILES.get('file')
        if not file_obj:
            return Response({'error': '未找到上传的文件。'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            df = pd.read_excel(file_obj, dtype=str).fillna('')
        except Exception as e:
            return Response({'error': f'无法解析Excel文件: {e}'}, status=status.HTTP_400_BAD_REQUEST)

        required_columns = {'stu_no', 'stu_name', 'password', 'grade', 'major'}
        if not required_columns.issubset(df.columns):
            missing = required_columns - set(df.columns)
            return Response({'error': f'Excel文件中缺少必需的列: {", ".join(missing)}'},
                            status=status.HTTP_400_BAD_REQUEST)

        students_to_create = []
        failed_entries = []

        existing_stu_nos = set(Student.objects.values_list('stu_no', flat=True))

        for index, row in df.iterrows():
            stu_no = row.get('stu_no', '').strip()
            stu_name = row.get('stu_name', '').strip()
            password = row.get('password', '').strip()
            grade = row.get('grade', '').strip()
            major_name = row.get('major', '').strip()
            phone = row.get('phone', '').strip()
            email = row.get('email', '').strip()

            row_num = index + 2

            if not all([stu_no, stu_name, password, grade, major_name]):
                failed_entries.append(
                    {'row': row_num, 'stu_no': stu_no, 'error': '缺少必填字段 (学号, 姓名, 密码, 年级, 专业)。'})
                continue

            if stu_no in existing_stu_nos:
                failed_entries.append({'row': row_num, 'stu_no': stu_no, 'error': f'学号 "{stu_no}" 已存在。'})
                continue

            try:
                major_obj, _ = Major.objects.get_or_create(major_name=major_name)

                student = Student(
                    stu_no=stu_no,
                    stu_name=stu_name,
                    grade=grade,
                    major=major_obj,
                    phone=phone if phone else None,
                    email=email if email else None,
                )
                student.set_password(password)
                students_to_create.append(student)

                existing_stu_nos.add(stu_no)

            except Exception as e:
                failed_entries.append({'row': row_num, 'stu_no': stu_no, 'error': f'创建学生对象时发生内部错误: {e}'})

        if students_to_create:
            with transaction.atomic():
                Student.objects.bulk_create(students_to_create)

        return Response({
            'message': f'处理完成。成功注册 {len(students_to_create)} 名学生。',
            'success_count': len(students_to_create),
            'failure_count': len(failed_entries),
            'failed_entries': failed_entries
        }, status=status.HTTP_201_CREATED)


class AdminUserListView(generics.ListAPIView):
    """
    管理员列表视图，只显示安全的字段
    """
    queryset = AdminUser.objects.all().order_by('-admin_id')
    serializer_class = UserProfileSerializer


class TeacherManagementViewSet(viewsets.ModelViewSet):
    """
    教师管理视图集，支持搜索、创建、更新、删除和批量删除。
    """
    queryset = teacher.objects.all().order_by('teacher_id')

    filter_backends = [filters.SearchFilter]
    search_fields = ['teacher_no', 'teacher_name']

    def get_serializer_class(self):
        """根据操作返回不同的序列化器。"""
        if self.action == 'list':
            return TeacherProfileSerializer
        return TeacherManagementSerializer

    @action(detail=False, methods=['post'], url_path='bulk-delete')
    @transaction.atomic
    def bulk_delete(self, request, *args, **kwargs):
        """
        ✅ 修正：批量删除教师前，先处理多活动关联数据
        """
        teacher_ids = request.data.get('ids')

        if not isinstance(teacher_ids, list) or not teacher_ids:
            return Response(
                {'error': '请求体中必须包含一个非空的 "ids" 列表。'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # ✅ 1. 清理这些教师在所有活动中的团队志愿
        Group.objects.filter(preferred_advisor_1_id__in=teacher_ids).update(preferred_advisor_1=None)
        Group.objects.filter(preferred_advisor_2_id__in=teacher_ids).update(preferred_advisor_2=None)
        Group.objects.filter(preferred_advisor_3_id__in=teacher_ids).update(preferred_advisor_3=None)

        # ✅ 2. 清理这些教师在所有活动中的最终指导关系
        Group.objects.filter(advisor_id__in=teacher_ids).update(advisor=None)

        # ✅ 3. 删除教师（外键级联会自动删除 TeacherGroupPreference 和 ProvisionalAssignment）
        queryset = self.get_queryset().filter(teacher_id__in=teacher_ids)
        deleted_count, _ = queryset.delete()

        return Response(
            {'message': f'成功删除 {deleted_count} 名教师及其所有活动关联数据。'},
            status=status.HTTP_200_OK
        )


class StudentFilter(django_filters.FilterSet):
    """
    ✅ 修正：多活动适配 - 支持按活动ID筛选团队
    """
    major_name = django_filters.CharFilter(field_name='major__major_name', lookup_expr='icontains')
    team_name = django_filters.CharFilter(method='filter_by_team_name')
    event_id = django_filters.NumberFilter(method='filter_by_event')

    class Meta:
        model = Student
        fields = ['grade', 'major_name', 'team_name', 'event_id']

    def filter_by_team_name(self, queryset, name, value):
        """
        按团队名称筛选学生（跨所有活动）
        """
        return queryset.filter(memberships__group__group_name__icontains=value).distinct()

    def filter_by_event(self, queryset, name, value):
        """
        按活动ID筛选学生（只返回参与该活动的学生）
        """
        return queryset.filter(
            Q(memberships__group__event_id=value) | Q(mutual_selection_events__event_id=value)
        ).distinct()


class StudentManagementViewSet(viewsets.ModelViewSet):
    """
    ✅ 修正：学生管理视图集，支持多活动场景
    """
    queryset = Student.objects.select_related('major').prefetch_related(
        'memberships__group__event',  # ✅ 改为 memberships（复数）
        'led_groups__event'  # ✅ 改为 led_groups（复数）
    ).all().order_by('stu_id')

    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_class = StudentFilter
    search_fields = ['stu_no', 'stu_name']

    def get_serializer_class(self):
        """根据不同的操作(action)，使用不同的序列化器。"""
        if self.action == 'list':
            return StudentListSerializer
        return StudentManagementSerializer

    @action(detail=False, methods=['post'], url_path='bulk-delete')
    @transaction.atomic
    def bulk_delete(self, request, *args, **kwargs):
        """
        ✅ 修正：批量删除学生前，先处理多活动场景下的团队数据
        """
        student_ids = request.data.get('ids')

        if not isinstance(student_ids, list) or not student_ids:
            return Response(
                {'error': '请求体中必须包含一个非空的 "ids" 列表。'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # ✅ 1. 找出这些学生在所有活动中担任队长的团队
        groups_led_by_students = Group.objects.filter(captain_id__in=student_ids)

        for group in groups_led_by_students:
            # 如果团队只有队长一人，删除团队
            if group.members.count() == 1:
                group.delete()
            else:
                # 如果团队有多人，将队长置空（需要手动重新指定）
                group.captain = None
                group.save()

        # ✅ 2. 删除这些学生在所有活动中的成员关系（级联会自动处理）
        GroupMembership.objects.filter(student_id__in=student_ids).delete()

        # ✅ 3. 删除学生
        queryset = self.get_queryset().filter(stu_id__in=student_ids)
        deleted_count, _ = queryset.delete()

        return Response(
            {'message': f'成功删除 {deleted_count} 名学生及其所有活动关联数据。'},
            status=status.HTTP_200_OK
        )


class MajorListView(generics.ListAPIView):
    """
    提供学生专业列表的视图
    """
    queryset = Major.objects.all()
    serializer_class = MajorSerializer


class MutualSelectionEventViewSet(viewsets.ModelViewSet):
    """
    ✅ 修正：互选活动管理视图集，完善多活动支持
    """
    queryset = MutualSelectionEvent.objects.prefetch_related(
        'teachers', 'students__major'
    ).annotate(
        teacher_count=Count('teachers', distinct=True),
        student_count=Count('students', distinct=True)
    ).all().order_by('-stu_start_time')

    filter_backends = [filters.SearchFilter, DjangoFilterBackend]
    search_fields = ['event_name']
    filterset_fields = {
        'stu_start_time': ['gte', 'lte'], 'stu_end_time': ['gte', 'lte'],
        'tea_start_time': ['gte', 'lte'], 'tea_end_time': ['gte', 'lte'],
    }

    def get_serializer_class(self):
        if self.action in ['list', 'retrieve']:
            return MutualSelectionEventListSerializer
        return MutualSelectionEventSerializer

    @transaction.atomic
    def update(self, request, *args, **kwargs):
        """
        ✅ 修正：重写 update 方法，安全地处理参与者列表的变更（多活动场景）
        """
        partial = kwargs.pop('partial', False)
        instance = self.get_object()

        # 1. 获取更新前的学生和教师ID集合
        original_student_ids = set(instance.students.values_list('pk', flat=True))
        original_teacher_ids = set(instance.teachers.values_list('pk', flat=True))

        # 2. 调用序列化器进行常规验证和更新
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)

        instance.refresh_from_db()

        # 3. 获取更新后的学生和教师ID集合
        current_student_ids = set(instance.students.values_list('pk', flat=True))
        current_teacher_ids = set(instance.teachers.values_list('pk', flat=True))

        # 4. 处理被移除的学生
        removed_student_ids = original_student_ids - current_student_ids
        if removed_student_ids:
            # ✅ 只影响当前活动的数据
            memberships_to_delete = GroupMembership.objects.filter(
                group__event=instance,
                student_id__in=removed_student_ids
            )

            # 检查这些学生是否在当前活动中担任队长
            for student_id in removed_student_ids:
                try:
                    group = Group.objects.get(captain_id=student_id, event=instance)
                    if group.members.count() > 1:
                        # 团队有多人，将队长置空
                        group.captain = None
                        group.save()
                    else:
                        # 团队只有队长一人，删除团队
                        group.delete()
                except Group.DoesNotExist:
                    pass

            # 删除成员关系
            memberships_to_delete.delete()

        # 5. 处理被移除的教师
        removed_teacher_ids = original_teacher_ids - current_teacher_ids
        if removed_teacher_ids:
            # ✅ 只影响当前活动的数据
            Group.objects.filter(event=instance, preferred_advisor_1_id__in=removed_teacher_ids).update(
                preferred_advisor_1=None)
            Group.objects.filter(event=instance, preferred_advisor_2_id__in=removed_teacher_ids).update(
                preferred_advisor_2=None)
            Group.objects.filter(event=instance, preferred_advisor_3_id__in=removed_teacher_ids).update(
                preferred_advisor_3=None)
            Group.objects.filter(event=instance, advisor_id__in=removed_teacher_ids).update(advisor=None)

        return Response(self.get_serializer(instance).data)

    @transaction.atomic
    def destroy(self, request, *args, **kwargs):
        """
        ✅ 修正：删除活动前，先删除该活动下的所有团队（多活动隔离）
        """
        instance = self.get_object()

        # ✅ 只删除当前活动的团队
        Group.objects.filter(event=instance).delete()

        self.perform_destroy(instance)

        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=False, methods=['post'], url_path='bulk-delete')
    @transaction.atomic
    def bulk_delete(self, request, *args, **kwargs):
        """
        ✅ 修正：批量删除活动，确保关联的团队也被一并删除（多活动隔离）
        """
        event_ids = request.data.get('ids')
        if not isinstance(event_ids, list) or not event_ids:
            return Response(
                {'error': '请求体中必须包含一个非空的 "ids" 列表。'},
                status=status.HTTP_400_BAD_REQUEST
            )

        queryset = self.get_queryset().filter(event_id__in=event_ids)

        # ✅ 只删除这些活动的团队
        Group.objects.filter(event__in=queryset).delete()

        deleted_count, _ = queryset.delete()

        return Response(
            {'message': f'成功删除 {deleted_count} 个互选活动及其所有关联团队。'},
            status=status.HTTP_200_OK
        )

    @action(detail=True, methods=['get'], url_path='statistics')
    def statistics(self, request, pk=None):
        """
        ✅ 新增：获取单个活动的统计信息
        """
        event = self.get_object()

        # 统计数据
        total_students = event.students.count()
        total_teachers = event.teachers.count()
        total_groups = Group.objects.filter(event=event).count()

        # 统计已组队学生
        grouped_student_ids = GroupMembership.objects.filter(
            group__event=event
        ).values_list('student_id', flat=True).distinct()
        grouped_students_count = len(grouped_student_ids)

        # 统计已分配导师的团队
        assigned_groups_count = Group.objects.filter(event=event, advisor__isnull=False).count()

        return Response({
            'event_id': event.event_id,
            'event_name': event.event_name,
            'total_students': total_students,
            'total_teachers': total_teachers,
            'total_groups': total_groups,
            'grouped_students_count': grouped_students_count,
            'ungrouped_students_count': total_students - grouped_students_count,
            'assigned_groups_count': assigned_groups_count,
            'unassigned_groups_count': total_groups - assigned_groups_count,
        })