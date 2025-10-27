from django.shortcuts import render
from django.contrib.auth import authenticate
from rest_framework import views, status
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken
from .models import teacher # 导入 teacher 模型
from .serializers import (
    TeacherLoginSerializer,  # 导入 TeacherLoginSerializer
    TeacherProfileSerializer   # 导入 TeacherProfileSerializer
)


class TeacherLoginView(views.APIView):
    permission_classes = [AllowAny]
    serializer_class = TeacherLoginSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)

        teacher_no = serializer.validated_data.get('teacher_no')
        password = serializer.validated_data.get('password')

        # 使用 teacher_no 作为 username 进行认证
        user = authenticate(request, username=teacher_no, password=password)

        if user and isinstance(user, teacher):
            # 为教师用户生成 token 并加入身份标识
            refresh = RefreshToken.for_user(user)
            refresh['user_type'] = 'teacher'

            return Response({
                'refresh': str(refresh),
                'access': str(refresh.access_token),
            }, status=status.HTTP_200_OK)
        else:
            return Response({'detail': '工号或密码错误。'}, status=status.HTTP_401_UNAUTHORIZED)


# --- 新增的教师查看自己信息的视图 ---
class TeacherProfileView(views.APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        # request.user 会被 simple-jwt 自动设置为当前登录的教师对象
        serializer = TeacherProfileSerializer(request.user)
        return Response(serializer.data)

    def put(self, request, *args, **kwargs):
        """处理学生更新个人信息的请求"""
        student_instance = request.user

        # 使用 partial=True 允许部分更新，用户不必提交所有字段
        serializer = TeacherProfileSerializer(
            instance=student_instance,
            data=request.data,
            partial=True
        )

        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response(serializer.data, status=status.HTTP_200_OK)
