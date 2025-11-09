from rest_framework import serializers
from .models import teacher

class TeacherLoginSerializer(serializers.Serializer):
    teacher_no = serializers.CharField(max_length=50)
    password = serializers.CharField(
        style={'input_type': 'password'},
        trim_whitespace=False
    )

    def validate(self, attrs):
        teacher_no = attrs.get('teacher_no')
        password = attrs.get('password')

        if not teacher_no or not password:
            raise serializers.ValidationError("必须提供工号和密码。")

        return attrs


class TeacherProfileSerializer(serializers.ModelSerializer):
    old_password = serializers.CharField(write_only=True, required=False, allow_blank=True)
    new_password = serializers.CharField(write_only=True, required=False, allow_blank=True, style={'input_type': 'password'})
    confirm_password = serializers.CharField(write_only=True, required=False, allow_blank=True, style={'input_type': 'password'})

    class Meta:
        model = teacher
        fields = (
            'teacher_id', 'teacher_no', 'teacher_name',
            'phone', 'email', 'research_direction', 'introduction',
            'old_password', 'new_password', 'confirm_password'
        )
        read_only_fields = ('teacher_id', 'teacher_no', 'teacher_name')

    def validate(self, data):
        """
        [核心逻辑] 在这里验证密码更改请求。
        """
        # self.instance 是当前正在被更新的教师对象
        user = self.instance
        old_password = data.get('old_password')
        new_password = data.get('new_password')
        confirm_password = data.get('confirm_password')

        # 只有当用户尝试设置新密码时，才执行密码验证
        if new_password:
            # 1. 检查是否提供了原密码
            if not old_password:
                raise serializers.ValidationError({'old_password': '要设置新密码，必须提供原密码。'})

            # 2. 验证原密码是否正确
            if not user.check_password(old_password):
                raise serializers.ValidationError({'old_password': '原密码错误。'})

            # 3. 验证新密码和确认密码是否一致
            if new_password != confirm_password:
                raise serializers.ValidationError({'confirm_password': '两次输入的新密码不一致。'})

        return data

    def update(self, instance, validated_data):
        """
        更新用户信息，并安全地处理密码。
        """
        # 使用 .pop() 安全地移除密码字段，防止它们被直接赋给模型
        new_password = validated_data.pop('new_password', None)
        # 其他密码字段也一并移除
        validated_data.pop('old_password', None)
        validated_data.pop('confirm_password', None)

        # 调用父类方法更新其他常规字段
        instance = super().update(instance, validated_data)

        # 如果验证通过的 new_password 存在，则设置新密码
        if new_password:
            instance.set_password(new_password)
            instance.save()

        return instance
