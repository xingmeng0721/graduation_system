from rest_framework import generics, status, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.views import APIView
from django.contrib.auth import get_user_model, authenticate, login, logout
from django.contrib.auth.hashers import check_password
from django.db import transaction
from django.db import models
from .models import StudentProfile, TeacherProfile
from .serializers import (
    UserSerializer, UserRegistrationSerializer, UserDetailSerializer,
    StudentProfileSerializer, TeacherProfileSerializer,
    TeacherListSerializer, StudentListSerializer, PasswordChangeSerializer
)

User = get_user_model()


class RegisterView(generics.CreateAPIView):
    """用户注册视图"""
    queryset = User.objects.all()
    serializer_class = UserRegistrationSerializer
    permission_classes = [permissions.AllowAny]
    
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        with transaction.atomic():
            user = serializer.save()
            
            # 根据角色创建相应的档案
            if user.role == 'student':
                StudentProfile.objects.create(user=user)
            elif user.role == 'teacher':
                TeacherProfile.objects.create(user=user)
        
        return Response(
            {'message': '注册成功', 'user': UserSerializer(user).data},
            status=status.HTTP_201_CREATED
        )


class LoginView(APIView):
    """用户登录视图"""
    permission_classes = [permissions.AllowAny]
    
    def post(self, request):
        username = request.data.get('username')
        password = request.data.get('password')
        
        if not username or not password:
            return Response(
                {'error': '用户名和密码不能为空'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        user = authenticate(username=username, password=password)
        if user:
            login(request, user)
            return Response({
                'message': '登录成功',
                'user': UserDetailSerializer(user).data
            })
        
        return Response(
            {'error': '用户名或密码错误'},
            status=status.HTTP_401_UNAUTHORIZED
        )


class LogoutView(APIView):
    """用户登出视图"""
    
    def post(self, request):
        logout(request)
        return Response({'message': '登出成功'})


class ProfileView(generics.RetrieveUpdateAPIView):
    """用户档案视图"""
    serializer_class = UserDetailSerializer
    
    def get_object(self):
        return self.request.user


class PasswordChangeView(APIView):
    """密码修改视图"""
    
    def post(self, request):
        serializer = PasswordChangeSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        user = request.user
        old_password = serializer.validated_data['old_password']
        new_password = serializer.validated_data['new_password']
        
        if not check_password(old_password, user.password):
            return Response(
                {'error': '原密码错误'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        user.set_password(new_password)
        user.save()
        
        return Response({'message': '密码修改成功'})


class StudentProfileView(generics.RetrieveUpdateAPIView):
    """学生档案视图"""
    serializer_class = StudentProfileSerializer
    
    def get_object(self):
        profile, created = StudentProfile.objects.get_or_create(user=self.request.user)
        return profile
    
    def get_permissions(self):
        if self.request.user.is_authenticated and self.request.user.is_student:
            return [permissions.IsAuthenticated()]
        return [permissions.DenyAll()]


class TeacherProfileView(generics.RetrieveUpdateAPIView):
    """教师档案视图"""
    serializer_class = TeacherProfileSerializer
    
    def get_object(self):
        profile, created = TeacherProfile.objects.get_or_create(user=self.request.user)
        return profile
    
    def get_permissions(self):
        if self.request.user.is_authenticated and self.request.user.is_teacher:
            return [permissions.IsAuthenticated()]
        return [permissions.DenyAll()]


class TeacherListView(generics.ListAPIView):
    """教师列表视图"""
    serializer_class = TeacherListSerializer
    
    def get_queryset(self):
        queryset = User.objects.filter(role='teacher').select_related('teacher_profile')
        
        # 筛选条件
        department = self.request.query_params.get('department')
        if department:
            queryset = queryset.filter(department__icontains=department)
        
        research_area = self.request.query_params.get('research_area')
        if research_area:
            queryset = queryset.filter(
                teacher_profile__research_areas__icontains=research_area
            )
        
        accepting_only = self.request.query_params.get('accepting_only')
        if accepting_only == 'true':
            queryset = queryset.filter(
                teacher_profile__is_accepting=True,
                teacher_profile__current_students__lt=models.F('teacher_profile__max_students')
            )
        
        return queryset.order_by('department', 'real_name')


class StudentListView(generics.ListAPIView):
    """学生列表视图"""
    serializer_class = StudentListSerializer
    
    def get_queryset(self):
        queryset = User.objects.filter(role='student').select_related('student_profile')
        
        # 筛选条件
        department = self.request.query_params.get('department')
        if department:
            queryset = queryset.filter(department__icontains=department)
        
        major = self.request.query_params.get('major')
        if major:
            queryset = queryset.filter(major__icontains=major)
        
        grade = self.request.query_params.get('grade')
        if grade:
            queryset = queryset.filter(grade=grade)
        
        return queryset.order_by('department', 'major', 'grade', 'real_name')


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def current_user_view(request):
    """获取当前用户信息"""
    serializer = UserDetailSerializer(request.user)
    return Response(serializer.data)
