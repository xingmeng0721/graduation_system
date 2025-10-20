from django.contrib.auth import authenticate
from rest_framework import generics, status, views, viewsets
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.parsers import MultiPartParser, FormParser
from django.contrib.auth.hashers import check_password, make_password
from .models import AdminUser
from .serializers import AdminUserSerializer, LoginSerializer, UserProfileSerializer, StudentManagementSerializer, \
    StudentListSerializer, MajorSerializer, GroupSerializer
import pandas as pd
import io
from django.http import HttpResponse
from django.db import transaction
from rest_framework.permissions import IsAuthenticated, AllowAny
from studentapp.models import Student, Major, Group


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


class AdminUserListView(generics.ListAPIView):
    """
    管理员列表视图，只显示安全的字段
    """
    queryset = AdminUser.objects.all().order_by('-admin_id')
    serializer_class = UserProfileSerializer # 使用安全的只读序列化器


class StudentManagementViewSet(viewsets.ModelViewSet):
    """
    学生管理列表视图，只显示安全的字段
    """
    queryset = Student.objects.all().order_by('stu_id')

    # 根据不同的操作(action)，使用不同的序列化器
    def get_serializer_class(self):
        if self.action == 'list':
            return StudentListSerializer
        return StudentManagementSerializer


class MajorListView(generics.ListAPIView):
    """
    提供学生专业列表的视图
    """
    queryset = Major.objects.all()
    serializer_class = MajorSerializer


class GroupListView(generics.ListAPIView):
    """
    提供学生分组列表的视图
    """
    queryset = Group.objects.all()
    serializer_class = GroupSerializer