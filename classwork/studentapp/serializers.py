from rest_framework import serializers
from .models import Student, Major

# 学生登录序列化器
class StudentLoginSerializer(serializers.Serializer):
    stu_no = serializers.CharField(required=True)
    password = serializers.CharField(required=True, write_only=True)

# 学生个人信息序列化器
class StudentProfileSerializer(serializers.ModelSerializer):
    major = serializers.StringRelatedField(read_only=True)

    class Meta:
        model = Student
        # [修复] 明确列出所有字段，并设置只读字段
        fields = ['stu_id', 'stu_no', 'stu_name', 'grade', 'phone', 'major', 'email']
        read_only_fields = ['stu_id', 'stu_no', 'stu_name', 'grade', 'major']