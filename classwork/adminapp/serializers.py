from rest_framework import serializers
from .models import AdminUser
from django.contrib.auth.hashers import make_password

from studentapp.models import Student, Major, Group # <--- 直接从应用名开始


class AdminUserSerializer(serializers.ModelSerializer):
    """
    管理员注册
    """
    class Meta:
        model = AdminUser
        fields = ['admin_id', 'admin_name', 'admin_username', 'admin_password']
        # 为了安全，密码字段设置为只写，不会在API响应中返回
        extra_kwargs = {
            'admin_password': {'write_only': True}
        }

    # 重写 create 方法，对密码进行哈希加密
    def create(self, validated_data):
        # 使用 Django 内置的 make_password 来加密
        validated_data['admin_password'] = make_password(validated_data.get('admin_password'))
        return super(AdminUserSerializer, self).create(validated_data)

class LoginSerializer(serializers.Serializer):
    """登录专用的序列化器，只用于数据校验"""
    admin_username = serializers.CharField(required=True)
    password = serializers.CharField(required=True)

class UserProfileSerializer(serializers.ModelSerializer):
    """
    用于显示管理员信息的只读序列化器
    """
    class Meta:
        model = AdminUser
        # 只包含安全的、可供前端显示的字段
        fields = ['admin_id', 'admin_name', 'admin_username']


class StudentManagementSerializer(serializers.ModelSerializer):
    """
   学生注册的
    """
    major = serializers.CharField(write_only=True, required=True, label="专业名称")
    class Meta:
        model = Student
        fields = ['stu_id', 'stu_no', 'stu_name', 'password', 'grade', 'phone', 'major']
        extra_kwargs = {
            'password': {'write_only': True, 'required': True}
        }

    def create(self, validated_data):
        major_name = validated_data.pop('major')
        major_obj, created = Major.objects.get_or_create(major_name=major_name)
        validated_data['major'] = major_obj
        student = Student.objects.create_user(**validated_data)
        return student

    def update(self, instance, validated_data):
        if 'major' in validated_data:
            major_name = validated_data.pop('major')
            major_obj, created = Major.objects.get_or_create(major_name=major_name)
            instance.major = major_obj
        password = validated_data.pop('password', None)
        if password:
            instance.set_password(password)

        # 更新其他字段
        return super().update(instance, validated_data)


class StudentListSerializer(serializers.ModelSerializer):
    """
   用于管理员查看学生列表的序列化器
    """
    # 将外键显示为名称而不是ID
    major_name = serializers.CharField(source='major.major_name', read_only=True)
    group_name = serializers.CharField(source='group.group_name', read_only=True)

    class Meta:
        model = Student
        fields = ['stu_id', 'stu_no', 'stu_name', 'grade', 'phone', 'is_gleader', 'major_name', 'group_name']

class MajorSerializer(serializers.ModelSerializer):
    """
   用于管理员查看专业列表的序列化器
    """
    class Meta:
        model = Major
        fields = '__all__'

class GroupSerializer(serializers.ModelSerializer):
    """
   用于管理员查看组别列表的序列化器
    """
    class Meta:
        model = Group
        fields = '__all__'