from rest_framework import serializers
from .models import Student

# 学生登录序列化器
class StudentLoginSerializer(serializers.Serializer):
    stu_no = serializers.CharField(required=True)
    password = serializers.CharField(required=True, write_only=True)

# 学生个人信息序列化器
class StudentProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = Student
        # 定义学生查看自己信息时可以看到的字段
        fields = ['stu_id', 'stu_no', 'stu_name', 'grade', 'phone',  'major', 'email']
        depth = 1 # depth = 1 会将外键关联的对象完整地序列化出来，而不是只给一个ID