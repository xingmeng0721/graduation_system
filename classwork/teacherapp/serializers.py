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
    class Meta:
        model = teacher
        fields = (
            'teacher_id', 'teacher_no', 'teacher_name',
            'phone', 'email', 'research_direction', 'introduction'
        )

