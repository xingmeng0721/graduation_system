from django.db.models import Count
from django.utils import timezone
import django_filters
from django.contrib.auth import authenticate
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import generics, status, views, viewsets,filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.parsers import MultiPartParser, FormParser
from django.contrib.auth.hashers import check_password, make_password
from .models import AdminUser, MutualSelectionEvent
from teacherapp.models import teacher
from .serializers import AdminUserSerializer, LoginSerializer, UserProfileSerializer, StudentManagementSerializer, \
    StudentListSerializer, MajorSerializer, TeacherManagementSerializer, \
    TeacherProfileSerializer, MutualSelectionEventListSerializer, MutualSelectionEventSerializer
import pandas as pd
import io
from django.http import HttpResponse
from django.db import transaction
from rest_framework.permissions import IsAuthenticated, AllowAny
from studentapp.models import Student, Major
from teamapp.models import Group


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
        # 创建一个包含示例数据的DataFrame
        data = {
            'admin_name': ['示例用户', 'John Doe'],
            'admin_username': ['example_user', 'johndoe'],
            'password': ['password123', 'another_secret']
        }
        df = pd.DataFrame(data)

        # 将DataFrame写入内存中的Excel文件
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name='Users')

        # 重置指针到文件开头
        output.seek(0)

        """"准备 HTTP 响应：
        output.seek(0) 将内存流的指针移回开头，以便读取其全部内容。
        创建一个 HttpResponse 对象，其内容是内存中的 Excel 文件数据。
        设置 content_type 为 application/vnd.openxmlformats-officedocument.spreadsheetml.sheet，告知浏览器这是一个 Excel 文件。
        设置 Content-Disposition 响应头为 attachment; filename="registration_template.xlsx"，这会使浏览器弹出文件下载对话框，并指定默认文件名为 registration_template.xlsx。
        返回响应：将构建好的 HttpResponse 对象返回给客户端，用户即可下载该模板文件"""
        # 创建HTTP响应
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

        # 检查必需的列是否存在
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

            # 简单的数据校验
            if not all([admin_name, admin_username, password]):
                return Response({'error': f'行 {index + 2}: 所有字段均为必填项。'}, status=status.HTTP_400_BAD_REQUEST)

            # 检查用户名和名称是否已存在
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

        # 如果所有行都验证通过，则一次性批量创建用户
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
            return Response({'error': f'Excel文件中缺少必需的列: {", ".join(missing)}'}, status=status.HTTP_400_BAD_REQUEST)

        teachers_to_create = []
        failed_entries = []
        existing_teacher_nos = set(teacher.objects.values_list('teacher_no', flat=True))

        for index, row in df.iterrows():
            row_num = index + 2
            teacher_no = row.get('teacher_no', '').strip()
            teacher_name = row.get('teacher_name', '').strip()
            password = row.get('password', '').strip()

            if not all([teacher_no, teacher_name, password]):
                failed_entries.append({'row': row_num, 'teacher_no': teacher_no, 'error': '缺少必填字段 (工号, 姓名, 密码)。'})
                continue

            if teacher_no in existing_teacher_nos:
                failed_entries.append({'row': row_num, 'teacher_no': teacher_no, 'error': f'工号 "{teacher_no}" 已存在。'})
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
                failed_entries.append({'row': row_num, 'teacher_no': teacher_no, 'error': f'创建教师对象时发生内部错误: {e}'})

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
        # 定义模板的列和示例数据
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

        # 创建内存中的Excel文件
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name='Students')
        output.seek(0)

        # 创建并返回HTTP响应
        response = HttpResponse(
            output.read(),
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        response['Content-Disposition'] = 'attachment; filename="student_registration_template.xlsx"'
        return response


class BulkRegisterStudentsView(views.APIView):
    """
    通过上传Excel文件批量注册学生。
    会自动跳过无效数据行，并报告错误。
    """
    parser_classes = (MultiPartParser, FormParser)

    def post(self, request, *args, **kwargs):
        file_obj = request.FILES.get('file')
        if not file_obj:
            return Response({'error': '未找到上传的文件。'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            df = pd.read_excel(file_obj, dtype=str).fillna('')  # 读取所有数据为字符串，并将NaN替换为空字符串
        except Exception as e:
            return Response({'error': f'无法解析Excel文件: {e}'}, status=status.HTTP_400_BAD_REQUEST)

        # 检查必需的列
        required_columns = {'stu_no', 'stu_name', 'password', 'grade', 'major'}
        if not required_columns.issubset(df.columns):
            missing = required_columns - set(df.columns)
            return Response({'error': f'Excel文件中缺少必需的列: {", ".join(missing)}'},
                            status=status.HTTP_400_BAD_REQUEST)

        students_to_create = []
        failed_entries = []

        # 预先获取所有已存在的学号，以减少数据库查询次数
        existing_stu_nos = set(Student.objects.values_list('stu_no', flat=True))

        for index, row in df.iterrows():
            stu_no = row.get('stu_no', '').strip()
            stu_name = row.get('stu_name', '').strip()
            password = row.get('password', '').strip()
            grade = row.get('grade', '').strip()
            major_name = row.get('major', '').strip()
            phone = row.get('phone', '').strip()
            email = row.get('email', '').strip()

            # --- 数据校验 ---
            row_num = index + 2  # Excel中的行号（考虑到表头）

            # 1. 检查必填字段
            if not all([stu_no, stu_name, password, grade, major_name]):
                failed_entries.append(
                    {'row': row_num, 'stu_no': stu_no, 'error': '缺少必填字段 (学号, 姓名, 密码, 年级, 专业)。'})
                continue

            # 2. 检查学号是否已存在
            if stu_no in existing_stu_nos:
                failed_entries.append({'row': row_num, 'stu_no': stu_no, 'error': f'学号 "{stu_no}" 已存在。'})
                continue

            # --- 准备数据 ---
            try:
                # 获取或创建专业对象
                major_obj, _ = Major.objects.get_or_create(major_name=major_name)

                # 创建Student对象（但不保存）
                student = Student(
                    stu_no=stu_no,
                    stu_name=stu_name,
                    grade=grade,
                    major=major_obj,
                    phone=phone if phone else None,
                    email=email if email else None,
                )
                student.set_password(password)  # 设置哈希密码
                students_to_create.append(student)

                # 将刚验证通过的学号加入集合，防止Excel内部有重复学号
                existing_stu_nos.add(stu_no)

            except Exception as e:
                failed_entries.append({'row': row_num, 'stu_no': stu_no, 'error': f'创建学生对象时发生内部错误: {e}'})

        # 使用事务一次性批量创建所有合法的学生
        if students_to_create:
            with transaction.atomic():
                Student.objects.bulk_create(students_to_create)

        # 构建最终的响应
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
    serializer_class = UserProfileSerializer # 使用安全的只读序列化器


class TeacherManagementViewSet(viewsets.ModelViewSet):
    """
    教师管理视图集，支持搜索、创建、更新、删除和批量删除。
    """
    queryset = teacher.objects.all().order_by('teacher_id')

    # 1. 启用搜索功能
    filter_backends = [filters.SearchFilter]

    # 2. 定义可以被搜索的字段
    search_fields = ['teacher_no', 'teacher_name']

    def get_serializer_class(self):
        """根据操作返回不同的序列化器。"""
        # 对于列表视图，使用只读的 Profile 序列化器
        if self.action == 'list':
            return TeacherProfileSerializer
        # 对于创建、更新等写操作，使用功能更全的管理序列化器
        return TeacherManagementSerializer

    # 3. 添加批量删除的自定义 action
    @action(detail=False, methods=['post'], url_path='bulk-delete')
    def bulk_delete(self, request, *args, **kwargs):
        """
        根据提供的教师ID列表，批量删除教师。
        请求体格式: { "ids": [1, 2, 3] }
        """
        teacher_ids = request.data.get('ids')

        if not isinstance(teacher_ids, list) or not teacher_ids:
            return Response(
                {'error': '请求体中必须包含一个非空的 "ids" 列表。'},
                status=status.HTTP_400_BAD_REQUEST
            )

        queryset = self.get_queryset().filter(teacher_id__in=teacher_ids)
        deleted_count, _ = queryset.delete()

        return Response(
            {'message': f'成功删除 {deleted_count} 名教师。'},
            status=status.HTTP_200_OK
        )




class StudentFilter(django_filters.FilterSet):
    major_name = django_filters.CharFilter(field_name='major__major_name', lookup_expr='icontains')
    team_name = django_filters.CharFilter(field_name='membership__group__group_name', lookup_expr='icontains')
    class Meta:
        model = Student
        fields = ['grade', 'major_name', 'team_name']


class StudentManagementViewSet(viewsets.ModelViewSet):
    """
    学生管理视图集，支持筛选、排序、单个和批量操作。
    """
    queryset = Student.objects.select_related(
        'major',
        'membership__group'
    ).prefetch_related(
        'led_group'
    ).all().order_by('stu_id')

    # 启用 django-filter 后端
    filter_backends = [DjangoFilterBackend,filters.SearchFilter]
    # 指定用于此视图集的 FilterSet 类
    filterset_class = StudentFilter
    search_fields = ['stu_no', 'stu_name']

    def get_serializer_class(self):
        """根据不同的操作(action)，使用不同的序列化器。"""
        if self.action == 'list':
            return StudentListSerializer
        return StudentManagementSerializer

    # 3. 新增：批量删除的自定义 action
    @action(detail=False, methods=['post'], url_path='bulk-delete')
    def bulk_delete(self, request, *args, **kwargs):
        """
        根据提供的学生ID列表，批量删除学生。
        期望的请求体格式: { "ids": [1, 2, 3] }
        """
        student_ids = request.data.get('ids')

        # 数据校验
        if not isinstance(student_ids, list) or not student_ids:
            return Response(
                {'error': '请求体中必须包含一个非空的 "ids" 列表。'},
                status=status.HTTP_400_BAD_REQUEST
            )


        queryset = self.get_queryset().filter(stu_id__in=student_ids)
        deleted_count, _ = queryset.delete()

        return Response(
            {'message': f'成功删除 {deleted_count} 名学生。'},
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
    互选活动管理视图集。
    支持:
    - 搜索: 根据活动名称 (`event_name`) 搜索。
    - 筛选: 根据时间范围进行筛选 (例如: ?start_time_after=...&end_time_before=...)。
    - 完整 CRUD 操作。
    - 批量删除。
    """
    # 预取相关对象以优化查询性能
    queryset = MutualSelectionEvent.objects.prefetch_related(
        'teachers', 'students__major'
    ).annotate(
        teacher_count=Count('teachers', distinct=True),
        student_count=Count('students', distinct=True)
    ).all().order_by('-start_time')

    # 配置搜索和筛选
    filter_backends = [filters.SearchFilter, DjangoFilterBackend]
    search_fields = ['event_name']
    filterset_fields = {
        'start_time': ['gte', 'lte'],  # 例如: ?start_time__gte=YYYY-MM-DD
        'end_time': ['gte', 'lte'],    # 例如: ?end_time__lte=YYYY-MM-DD
    }

    def get_serializer_class(self):
        """
        根据不同的操作返回不同的序列化器。
        - 列表/详情视图使用只读、信息丰富的序列化器。
        - 创建/更新视图使用可写的序列化器。
        """
        if self.action in ['list', 'retrieve']:
            return MutualSelectionEventListSerializer
        return MutualSelectionEventSerializer

    @action(detail=False, methods=['post'], url_path='bulk-delete')
    def bulk_delete(self, request, *args, **kwargs):
        """
        根据提供的活动ID列表，批量删除互选活动。
        请求体格式: { "ids": [1, 2, 3] }
        """
        event_ids = request.data.get('ids')

        if not isinstance(event_ids, list) or not event_ids:
            return Response(
                {'error': '请求体中必须包含一个非空的 "ids" 列表。'},
                status=status.HTTP_400_BAD_REQUEST
            )

        queryset = self.get_queryset().filter(event_id__in=event_ids)
        deleted_count, _ = queryset.delete()

        return Response(
            {'message': f'成功删除 {deleted_count} 个互选活动。'},
            status=status.HTTP_200_OK
        )

    @action(detail=True, methods=['post'], url_path='auto-assign')
    def auto_assign(self, request, *args, **kwargs):
        """
        对单个已过期的互选活动执行自动分配的占位符接口。
        """
        event = self.get_object()

        # 简单检查活动是否结束
        if event.end_time > timezone.now():
            return Response({'error': '该活动尚未结束，不能进行自动分配。'}, status=400)

        # 返回一个模拟的成功响应
        return Response({
            'message': '自动分配功能尚未实现，但接口已通。',
            'assigned_count': 0,
            'unassigned_count': len(event.students.all()),
            'unassigned_students': [{'stu_name': s.stu_name} for s in event.students.all()],
        }, status=200)