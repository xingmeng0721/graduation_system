from rest_framework import serializers
from .models import AdminUser, MutualSelectionEvent
from django.contrib.auth.hashers import make_password
from studentapp.models import Student, Major
from teacherapp.models import teacher
from teamapp.models import Group

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

class TeacherManagementSerializer(serializers.ModelSerializer):
    """
    用于管理员创建或更新教师信息的序列化器。
    """
    class Meta:
        model = teacher
        # 包含所有可写字段
        fields = [
            'teacher_id', 'teacher_no', 'teacher_name', 'password',
            'phone', 'email', 'research_direction', 'introduction'
        ]
        # 'read_only_fields' is not needed if we define write behavior in extra_kwargs

        extra_kwargs = {
            'password': {'write_only': True, 'required': True},
            # 将非必填字段明确标记出来
            'phone': {'required': False, 'allow_blank': True},
            'email': {'required': False, 'allow_blank': True},
            'research_direction': {'required': False, 'allow_blank': True},
            'introduction': {'required': False, 'allow_blank': True},
        }

    def create(self, validated_data):
        # 使用我们自定义的 Manager 来创建用户，确保密码被正确哈希
        user = teacher.objects.create_user(**validated_data)
        return user

    def update(self, instance, validated_data):
        # 处理密码更新
        password = validated_data.pop('password', None)
        if password:
            instance.set_password(password)

        # 调用父类的 update 方法来更新其他字段
        return super().update(instance, validated_data)


class TeacherProfileSerializer(serializers.ModelSerializer):
    """
    用于显示教师公开信息的序列化器。
    """
    class Meta:
        model = teacher
        fields = (
            'teacher_id', 'teacher_no', 'teacher_name',
            'phone', 'email', 'research_direction', 'introduction'
        )


class StudentManagementSerializer(serializers.ModelSerializer):
    """
   学生注册的
    """
    major = serializers.CharField(write_only=True, required=True, label="专业名称")
    class Meta:
        model = Student
        fields = ['stu_id', 'stu_no', 'stu_name', 'password', 'grade', 'phone', 'major','email']
        extra_kwargs = {
            'password': {'write_only': True, 'required': True},
            'phone': {'required': False, 'allow_blank': True},
            'email': {'required': False, 'allow_blank': True}
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
    team_info = serializers.SerializerMethodField()
    is_captain = serializers.SerializerMethodField()

    class Meta:
        model = Student
        fields = [
            'stu_id', 'stu_no', 'stu_name', 'grade', 'phone', 'email',
            'major_name', 'team_info', 'is_captain'
        ]

    def get_team_info(self, obj: Student):
        """
        获取学生所在的团队信息。
        通过检查 'membership' 反向关系是否存在来判断学生是否已分组。
        """
        # hasattr 检查可以防止因未分组学生缺少 'membership' 属性而引发的错误
        if hasattr(obj, 'membership') and obj.membership:
            return {
                'id': obj.membership.group.group_id,
                'name': obj.membership.group.group_name
            }
        return None  # 如果学生未加入任何团队，则返回 null

    def get_is_captain(self, obj: Student):
        """
        判断学生是否为队长。
        通过检查 'led_group' 反向 OneToOne 关系是否存在来判断。
        """
        return hasattr(obj, 'led_group') and obj.led_group is not None

class MajorSerializer(serializers.ModelSerializer):
    """
   用于管理员查看专业列表的序列化器
    """
    class Meta:
        model = Major
        fields = '__all__'


class MutualSelectionEventSerializer(serializers.ModelSerializer):
    """
    用于创建和更新互选活动的序列化器。
    """
    # 使用只写的字段来接收教师和学生的ID列表
    teachers = serializers.PrimaryKeyRelatedField(
        queryset=teacher.objects.all(),
        many=True,
        write_only=True,
        label="参与教师ID列表"
    )
    students = serializers.PrimaryKeyRelatedField(
        queryset=Student.objects.all(),
        many=True,
        write_only=True,
        label="参与学生ID列表"
    )

    class Meta:
        model = MutualSelectionEvent
        fields = ['event_id', 'event_name', 'start_time', 'end_time', 'teachers', 'students']

    def validate(self, data):
        """
        校验开始时间是否早于结束时间。
        """
        if 'start_time' in data and 'end_time' in data:
            if data['start_time'] >= data['end_time']:
                raise serializers.ValidationError("结束时间必须晚于开始时间。")
        return data


class MutualSelectionEventListSerializer(serializers.ModelSerializer):
    """
    用于展示互选活动列表和详情的序列化器。
    """
    # 使用嵌套序列化器来显示教师和学生的详细信息
    teachers = TeacherProfileSerializer(many=True, read_only=True)
    students = StudentListSerializer(many=True, read_only=True)

    class Meta:
        model = MutualSelectionEvent
        fields = ['event_id', 'event_name', 'start_time', 'end_time', 'teachers', 'students']