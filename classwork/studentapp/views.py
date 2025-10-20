from django.contrib.auth import authenticate
from rest_framework import views, status
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken
from .models import Student
from .serializers import StudentLoginSerializer, StudentProfileSerializer


class StudentLoginView(views.APIView):
    permission_classes = [AllowAny]
    serializer_class = StudentLoginSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)

        stu_no = serializer.validated_data.get('stu_no')
        password = serializer.validated_data.get('password')

        user = authenticate(request, username=stu_no, password=password)

        if user and isinstance(user, Student):
            # --- 关键：为学生用户也加入身份标识 ---
            # for_user 会自动处理 user_id
            refresh = RefreshToken.for_user(user)
            refresh['user_type'] = 'student'
            # --- 结束 ---

            return Response({
                'refresh': str(refresh),
                'access': str(refresh.access_token),
            }, status=status.HTTP_200_OK)
        else:
            return Response({'detail': '学号或密码错误。'}, status=status.HTTP_401_UNAUTHORIZED)


# 学生查看自己信息的视图
class StudentProfileView(views.APIView):
    permission_classes = [IsAuthenticated]  # 必须登录才能访问

    def get(self, request, *args, **kwargs):
        # request.user 会被 simple-jwt 自动设置为当前登录的学生对象
        serializer = StudentProfileSerializer(request.user)
        return Response(serializer.data)