from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import StudentProfile, TeacherProfile

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    """用户基础序列化器"""
    
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'real_name', 'student_id',
                 'phone_number', 'department', 'major', 'grade', 'role',
                 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']


class UserRegistrationSerializer(serializers.ModelSerializer):
    """用户注册序列化器"""
    password = serializers.CharField(write_only=True, min_length=6)
    password_confirm = serializers.CharField(write_only=True)
    
    class Meta:
        model = User
        fields = ['username', 'email', 'password', 'password_confirm',
                 'real_name', 'student_id', 'phone_number',
                 'department', 'major', 'grade', 'role']
    
    def validate(self, attrs):
        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError("密码确认不匹配")
        return attrs
    
    def create(self, validated_data):
        validated_data.pop('password_confirm')
        password = validated_data.pop('password')
        user = User.objects.create_user(**validated_data)
        user.set_password(password)
        user.save()
        return user


class StudentProfileSerializer(serializers.ModelSerializer):
    """学生档案序列化器"""
    user = UserSerializer(read_only=True)
    
    class Meta:
        model = StudentProfile
        fields = ['id', 'user', 'gpa', 'research_interests', 'skills', 'introduction']


class TeacherProfileSerializer(serializers.ModelSerializer):
    """教师档案序列化器"""
    user = UserSerializer(read_only=True)
    can_accept_more_students = serializers.ReadOnlyField()
    
    class Meta:
        model = TeacherProfile
        fields = ['id', 'user', 'title', 'research_areas', 'max_students',
                 'current_students', 'introduction', 'requirements',
                 'is_accepting', 'can_accept_more_students']


class UserDetailSerializer(serializers.ModelSerializer):
    """用户详细信息序列化器"""
    student_profile = StudentProfileSerializer(read_only=True)
    teacher_profile = TeacherProfileSerializer(read_only=True)
    
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'real_name', 'student_id',
                 'phone_number', 'department', 'major', 'grade', 'role',
                 'created_at', 'updated_at', 'student_profile', 'teacher_profile']
        read_only_fields = ['id', 'created_at', 'updated_at']


class TeacherListSerializer(serializers.ModelSerializer):
    """教师列表序列化器"""
    teacher_profile = TeacherProfileSerializer(read_only=True)
    
    class Meta:
        model = User
        fields = ['id', 'real_name', 'department', 'teacher_profile']


class StudentListSerializer(serializers.ModelSerializer):
    """学生列表序列化器"""
    student_profile = StudentProfileSerializer(read_only=True)
    
    class Meta:
        model = User
        fields = ['id', 'real_name', 'student_id', 'department', 'major', 'grade', 'student_profile']


class PasswordChangeSerializer(serializers.Serializer):
    """密码修改序列化器"""
    old_password = serializers.CharField()
    new_password = serializers.CharField(min_length=6)
    new_password_confirm = serializers.CharField()
    
    def validate(self, attrs):
        if attrs['new_password'] != attrs['new_password_confirm']:
            raise serializers.ValidationError("新密码确认不匹配")
        return attrs