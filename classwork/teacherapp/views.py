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
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.exceptions import TokenError


class TeacherLoginView(views.APIView):
    permission_classes = [AllowAny]
    serializer_class = TeacherLoginSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)

        teacher_no = serializer.validated_data.get('teacher_no')
        password = serializer.validated_data.get('password')

        try:
            teacher_user = teacher.objects.get(teacher_no=teacher_no)
        except teacher.DoesNotExist:
            return Response(
                {'detail': '工号或密码错误。'},
                status=status.HTTP_401_UNAUTHORIZED
            )

        if not teacher_user.check_password(password):
            return Response(
                {'detail': '工号或密码错误。'},
                status=status.HTTP_401_UNAUTHORIZED
            )

        refresh = RefreshToken()
        refresh['user_id'] = teacher_user.teacher_id
        refresh['user_type'] = 'teacher'

        return Response({
            'refresh': str(refresh),
            'access': str(refresh.access_token),
        }, status=status.HTTP_200_OK)


# --- 新增的教师查看自己信息的视图 ---
class TeacherProfileView(views.APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        # request.user 会被 simple-jwt 自动设置为当前登录的教师对象
        serializer = TeacherProfileSerializer(request.user)
        return Response(serializer.data)

    def put(self, request, *args, **kwargs):

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


@api_view(['POST'])
@permission_classes([AllowAny])
def refresh_teacher_token(request):
    """教师Token刷新接口"""
    refresh_token = request.data.get('refresh')

    if not refresh_token:
        return Response(
            {'error': '需要提供refresh token'},
            status=status.HTTP_400_BAD_REQUEST
        )

    try:
        refresh = RefreshToken(refresh_token)

        # 验证是否是教师的token
        if refresh.get('user_type') != 'teacher':
            return Response(
                {'error': '用户类型不匹配'},
                status=status.HTTP_401_UNAUTHORIZED
            )

        # ✅ 生成新的access token
        new_access_token = str(refresh.access_token)

        return Response({
            'access': new_access_token,
        }, status=status.HTTP_200_OK)

    except TokenError as e:
        return Response(
            {'error': str(e)},
            status=status.HTTP_401_UNAUTHORIZED
        )
    except Exception as e:
        return Response(
            {'error': '刷新token失败'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
