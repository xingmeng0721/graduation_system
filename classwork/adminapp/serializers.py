from django.db.models import Q
from rest_framework import serializers
from .models import AdminUser, MutualSelectionEvent
from django.contrib.auth.hashers import make_password
from django.utils import timezone
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
        extra_kwargs = {
            'admin_password': {'write_only': True}
        }

    # 重写 create 方法，对密码进行哈希加密
    def create(self, validated_data):
        validated_data['admin_password'] = make_password(validated_data.get('admin_password'))
        return super(AdminUserSerializer, self).create(validated_data)

class LoginSerializer(serializers.Serializer):
    """
    登录专用的序列化器，只用于数据校验
    """
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

        extra_kwargs = {
            'password': {'write_only': True, 'required': True},
            'phone': {'required': False, 'allow_blank': True},
            'email': {'required': False, 'allow_blank': True},
            'research_direction': {'required': False, 'allow_blank': True},
            'introduction': {'required': False, 'allow_blank': True},
        }



    def create(self, validated_data):
        user = teacher.objects.create_user(**validated_data)
        return user

    def __init__(self, *args, **kwargs):
        """让更新教师信息时 password 变为可选。"""
        super().__init__(*args, **kwargs)
        if self.instance:  # instance 存在说明是更新操作
            self.fields['password'].required = False

    def update(self, instance, validated_data):
        password = validated_data.pop('password', None)
        if password:
            instance.set_password(password)

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
            'password': {'write_only': True, 'required': False, 'allow_blank': True},
            'phone': {'required': False, 'allow_blank': True},
            'email': {'required': False, 'allow_blank': True}
        }

    def create(self, validated_data):
        major_name = validated_data.pop('major')
        major_obj, created = Major.objects.get_or_create(major_name=major_name)
        validated_data['major'] = major_obj
        password = validated_data.pop('password', '').strip()
        stu_no = validated_data.get('stu_no')
        if not password:
            if not stu_no or len(stu_no) < 3:
                raise serializers.ValidationError({'stu_no': '学号长度不足3位，无法自动生成默认密码。'})
            password = stu_no[-3:]

        student = Student.objects.create(**validated_data)
        student.set_password(password)
        student.save()
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

class SimpleStudentSerializer(serializers.ModelSerializer):
    """
    用于嵌套在其他序列化器中的简化版学生信息序列化器。
    """
    major_name = serializers.CharField(source='major.major_name', read_only=True)

    class Meta:
        model = Student
        fields = ['stu_id', 'stu_no', 'stu_name', 'major_name'] # 只包含必要信息

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
        fields = ['event_id', 'event_name', 'stu_start_time', 'stu_end_time',
                  'tea_start_time', 'tea_end_time', 'teacher_choice_limit','group_member_limit',
                  'teachers', 'students']

        extra_kwargs = {
            'teacher_choice_limit': {'required': False} , # 默认为 5，非必
            'group_member_limit': {'required': False},  # 默认为5，非必填
        }

    def validate(self, data):
        """
        复合校验:
        1. 校验时间合法性：结束时间必须晚于开始时间。
        2. 校验唯一性：一个学生或老师在同一时间只能参加一个未结束的活动。
        """
        # --- 1. 时间合法性校验 ---
        if 'stu_start_time' in data and 'stu_end_time' in data and data['stu_start_time'] >= data['stu_end_time']:
            raise serializers.ValidationError("学生截止时间必须晚于学生开始时间。")
        if 'tea_start_time' in data and 'tea_end_time' in data and data['tea_start_time'] >= data['tea_end_time']:
            raise serializers.ValidationError("教师截止时间必须晚于教师开始时间。")

        # --- 2. 参与者唯一性校验 ---
        now = timezone.now()

        # 确定要检查的学生和教师列表
        students_to_check = data.get('students', [])
        teachers_to_check = data.get('teachers', [])

        # 构建查询，查找所有尚未完全结束的活动
        # 一个活动只要学生或老师的结束时间晚于现在，就视为“活跃”
        active_events_query = MutualSelectionEvent.objects.filter(
            Q(stu_end_time__gt=now) | Q(tea_end_time__gt=now)
        )

        # 如果是更新操作，需要排除当前正在编辑的活动实例
        if self.instance:
            active_events_query = active_events_query.exclude(pk=self.instance.pk)

        # 检查学生
        if students_to_check:
            conflicting_students = active_events_query.filter(
                students__in=students_to_check
            ).values_list('students__stu_name', flat=True).distinct()

            if conflicting_students:
                raise serializers.ValidationError(
                    f"以下学生已参加了其他未结束的活动，不能重复添加: {', '.join(conflicting_students)}"
                )

        # 检查教师
        if teachers_to_check:
            conflicting_teachers = active_events_query.filter(
                teachers__in=teachers_to_check
            ).values_list('teachers__teacher_name', flat=True).distinct()

            if conflicting_teachers:
                raise serializers.ValidationError(
                    f"以下教师已参加了其他未结束的活动，不能重复添加: {', '.join(conflicting_teachers)}"
                )

        return data


class MutualSelectionEventListSerializer(serializers.ModelSerializer):
    teachers = TeacherProfileSerializer(many=True, read_only=True)
    students = SimpleStudentSerializer(many=True, read_only=True)
    teacher_count = serializers.IntegerField(read_only=True)
    student_count = serializers.IntegerField(read_only=True)
    status = serializers.SerializerMethodField()

    class Meta:
        model = MutualSelectionEvent
        # [修改] 增加了 teacher_choice_limit 字段
        fields = [
            'event_id', 'event_name', 'stu_start_time', 'stu_end_time',
            'tea_start_time', 'tea_end_time', 'teacher_choice_limit', 'status',
            'teacher_count', 'student_count', 'group_member_limit','teachers', 'students'
        ]


    def get_status(self, obj: MutualSelectionEvent) -> str:
        now = timezone.now()
        if obj.stu_start_time > now and obj.tea_start_time > now:
            return "未开始"
        elif obj.stu_end_time < now and obj.tea_end_time < now:
            return "已结束"
        else:
            return "进行中"