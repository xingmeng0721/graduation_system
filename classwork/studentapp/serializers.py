from rest_framework import serializers
from .models import Student, Major

# 学生登录序列化器
class StudentLoginSerializer(serializers.Serializer):
    stu_no = serializers.CharField(required=True)
    password = serializers.CharField(required=True, write_only=True)

# 学生个人信息序列化器
class StudentProfileSerializer(serializers.ModelSerializer):
    old_password = serializers.CharField(write_only=True, required=False, allow_blank=True)
    new_password = serializers.CharField(write_only=True, required=False, allow_blank=True,
                                         style={'input_type': 'password'})
    confirm_password = serializers.CharField(write_only=True, required=False, allow_blank=True,
                                             style={'input_type': 'password'})

    major = serializers.StringRelatedField(read_only=True)

    class Meta:
        model = Student
        fields = [
            'stu_id', 'stu_no', 'stu_name', 'grade', 'phone', 'major', 'email',
            'old_password', 'new_password', 'confirm_password'
        ]
        read_only_fields = ['stu_id', 'stu_no', 'stu_name', 'grade', 'major']

    def validate(self, data):
        """
        [新增] 在这里验证密码更改请求。
        """
        user = self.instance
        old_password = data.get('old_password')
        new_password = data.get('new_password')
        confirm_password = data.get('confirm_password')

        if new_password:
            if not old_password:
                raise serializers.ValidationError({'old_password': '要设置新密码，必须提供原密码。'})
            if not user.check_password(old_password):
                raise serializers.ValidationError({'old_password': '原密码错误。'})
            if new_password != confirm_password:
                raise serializers.ValidationError({'confirm_password': '两次输入的新密码不一致。'})

        return data

    def update(self, instance, validated_data):
        """
        [新增] 重写 update 方法以正确处理密码。
        """
        new_password = validated_data.pop('new_password', None)
        validated_data.pop('old_password', None)
        validated_data.pop('confirm_password', None)

        instance = super().update(instance, validated_data)

        if new_password:
            instance.set_password(new_password)
            instance.save()

        return instance