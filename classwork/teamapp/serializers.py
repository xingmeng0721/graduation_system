from rest_framework import serializers
from .models import Group, GroupMembership
from studentapp.models import Student
from teacherapp.models import teacher
from adminapp.models import MutualSelectionEvent


# --- 用于嵌套显示的简化序列化器 ---

class TeamMemberSerializer(serializers.ModelSerializer):
    """用于显示团队成员信息的简化序列化器"""
    is_captain = serializers.SerializerMethodField()

    class Meta:
        model = Student
        fields = ['stu_id', 'stu_no', 'stu_name', 'is_captain']

    def get_is_captain(self, obj):
        return hasattr(obj, 'led_group') and obj.led_group is not None


class TeamAdvisorSerializer(serializers.ModelSerializer):
    """用于显示导师信息的简化序列化器"""

    class Meta:
        model = teacher
        fields = [
            'teacher_id',
            'teacher_name',
            'email',
            'research_direction',
            'introduction',
            'phone',
        ]


# --- 新增：用于显示可组队队友的序列化器 ---

class AvailableTeammateSerializer(serializers.ModelSerializer):
    """用于显示当前活动中、尚未组队的学生列表"""
    major_name = serializers.CharField(source='major.major_name', read_only=True)

    class Meta:
        model = Student
        fields = ['stu_id', 'stu_no', 'stu_name', 'major_name']


# --- 核心的团队信息序列化器 ---

class GroupDetailSerializer(serializers.ModelSerializer):
    """用于显示团队完整信息的序列化器"""
    captain = TeamMemberSerializer(read_only=True)
    members = TeamMemberSerializer(many=True, read_only=True)
    advisor = TeamAdvisorSerializer(read_only=True)
    preferred_advisor_1 = TeamAdvisorSerializer(read_only=True)
    preferred_advisor_2 = TeamAdvisorSerializer(read_only=True)
    preferred_advisor_3 = TeamAdvisorSerializer(read_only=True)
    event_name = serializers.CharField(source='event.event_name', read_only=True)
    member_count = serializers.SerializerMethodField()

    class Meta:
        model = Group
        fields = [
            'group_id', 'group_name', 'project_title', 'project_description',
            'event_name', 'captain', 'members', 'member_count',
            'advisor', 'preferred_advisor_1', 'preferred_advisor_2', 'preferred_advisor_3'
        ]

    def get_member_count(self, obj):
        return obj.members.count()


class GroupCreateUpdateSerializer(serializers.ModelSerializer):
    """用于创建和更新团队的序列化器，包含完整的验证逻辑"""

    # [修复] 字段名与 Meta.fields 保持一致
    preferred_advisor_1_id = serializers.PrimaryKeyRelatedField(
        queryset=teacher.objects.all(), allow_null=True, required=False, source='preferred_advisor_1'
    )
    preferred_advisor_2_id = serializers.PrimaryKeyRelatedField(
        queryset=teacher.objects.all(), allow_null=True, required=False, source='preferred_advisor_2'
    )
    preferred_advisor_3_id = serializers.PrimaryKeyRelatedField(
        queryset=teacher.objects.all(), allow_null=True, required=False, source='preferred_advisor_3'
    )

    class Meta:
        model = Group
        # [修复] Meta.fields 必须包含序列化器中定义的字段名
        fields = [
            'group_name', 'project_title', 'project_description',
            'preferred_advisor_1_id', 'preferred_advisor_2_id', 'preferred_advisor_3_id'
        ]

    def validate(self, data):
        active_event = self.context.get('active_event')
        if not active_event:
            raise serializers.ValidationError("当前没有正在进行的互选活动。")

        available_teachers = active_event.teachers.all()
        for i in range(1, 4):
            advisor = data.get(f'preferred_advisor_{i}')
            if advisor and advisor not in available_teachers:
                raise serializers.ValidationError(f"选择的志愿导师 '{advisor.teacher_name}' 未参与当前活动。")

        # 2. 验证团队名称唯一性
        group_name = data.get('group_name')
        if group_name:
            query = Group.objects.filter(event=active_event, group_name=group_name)
            if self.instance:
                query = query.exclude(pk=self.instance.pk)
            if query.exists():
                raise serializers.ValidationError(f"团队名称 '{group_name}' 在本次活动中已被使用。")

        return data