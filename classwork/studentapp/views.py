import random
from django.contrib.auth import authenticate
from rest_framework import views, status
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken
from .models import Student, EmailVerifyCode
from .serializers import StudentLoginSerializer, StudentProfileSerializer
from django.core.mail import send_mail
from classwork import settings
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.exceptions import TokenError


class StudentLoginView(views.APIView):
    permission_classes = [AllowAny]
    serializer_class = StudentLoginSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)

        stu_no = serializer.validated_data.get('stu_no')
        password = serializer.validated_data.get('password')


        try:
            student = Student.objects.get(stu_no=stu_no)
        except Student.DoesNotExist:
            return Response(
                {'detail': '学号或密码错误。'},
                status=status.HTTP_401_UNAUTHORIZED
            )

        if not student.check_password(password):
            return Response(
                {'detail': '学号或密码错误。'},
                status=status.HTTP_401_UNAUTHORIZED
            )

        refresh = RefreshToken()
        refresh['user_id'] = student.stu_id
        refresh['user_type'] = 'student'

        return Response({
            'refresh': str(refresh),
            'access': str(refresh.access_token),
        }, status=status.HTTP_200_OK)

class SendResetCodeView(views.APIView):
    """发送重置密码验证码（邮箱 + 姓名验证）"""
    permission_classes = [AllowAny]

    def post(self, request):
        stu_name = request.data.get("stu_name")
        email = request.data.get("email")

        if not stu_name or not email:
            return Response({"error": "姓名和邮箱不能为空"}, status=status.HTTP_400_BAD_REQUEST)

        # 验证姓名与邮箱是否匹配数据库
        try:
            student = Student.objects.get(stu_name=stu_name, email=email)
        except Student.DoesNotExist:
            return Response({"error": "姓名与邮箱不匹配或未注册"}, status=status.HTTP_404_NOT_FOUND)

        # 生成6位验证码
        code = ''.join([str(random.randint(0, 9)) for _ in range(6)])

        # 保存验证码（同邮箱更新）
        EmailVerifyCode.objects.update_or_create(email=email, defaults={"code": code})

        # 发送邮件
        send_mail(
            subject="找回密码验证码",
            message=f"亲爱的 {stu_name}，\n您正在尝试重置密码，验证码是：{code}（10分钟内有效）。",
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[email],
        )

        return Response({"message": "验证码已发送至邮箱"}, status=status.HTTP_200_OK)

class ResetPasswordByCodeView(views.APIView):
    """通过验证码重置密码"""
    permission_classes = [AllowAny]

    def post(self, request):
        stu_name = request.data.get("stu_name")
        email = request.data.get("email")
        code = request.data.get("code")
        new_password = request.data.get("password")

        if not all([stu_name, email, code, new_password]):
            return Response({"error": "姓名、邮箱、验证码和新密码都不能为空"}, status=status.HTTP_400_BAD_REQUEST)

        # 查验证码
        try:
            verify_obj = EmailVerifyCode.objects.get(email=email)
        except EmailVerifyCode.DoesNotExist:
            return Response({"error": "请先获取验证码"}, status=status.HTTP_400_BAD_REQUEST)

        # 检查验证码是否过期/错误
        if verify_obj.is_expired():
            return Response({"error": "验证码已过期"}, status=status.HTTP_400_BAD_REQUEST)
        if verify_obj.code != code:
            return Response({"error": "验证码错误"}, status=status.HTTP_400_BAD_REQUEST)

        # 检查姓名和邮箱是否匹配学生
        try:
            student = Student.objects.get(stu_name=stu_name, email=email)
        except Student.DoesNotExist:
            return Response({"error": "姓名与邮箱不匹配"}, status=status.HTTP_404_NOT_FOUND)

        # 更新密码
        student.set_password(new_password)
        student.save()
        verify_obj.delete()  # 删除验证码

        return Response({"message": "密码重置成功"}, status=status.HTTP_200_OK)


# 学生查看自己信息的视图
class StudentProfileView(views.APIView):
    permission_classes = [IsAuthenticated]  # 必须登录才能访问

    def get(self, request, *args, **kwargs):
        # request.user 会被 simple-jwt 自动设置为当前登录的学生对象
        serializer = StudentProfileSerializer(request.user)
        return Response(serializer.data)

    def put(self, request, *args, **kwargs):
        """处理学生更新个人信息的请求"""
        student_instance = request.user

        # 使用 partial=True 允许部分更新，用户不必提交所有字段
        serializer = StudentProfileSerializer(
            instance=student_instance,
            data=request.data,
            partial=True
        )

        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response(serializer.data, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([AllowAny])
def refresh_student_token(request):
    """学生Token刷新接口"""
    refresh_token = request.data.get('refresh')

    if not refresh_token:
        return Response(
            {'error': '需要提供refresh token'},
            status=status.HTTP_400_BAD_REQUEST
        )

    try:
        refresh = RefreshToken(refresh_token)

        # 验证是否是学生的token
        if refresh.get('user_type') != 'student':
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




