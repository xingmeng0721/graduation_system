from rest_framework import serializers
from .models import Group, GroupMembership, ProvisionalAssignment
from studentapp.models import Student
from teacherapp.models import teacher
from adminapp.models import MutualSelectionEvent


# --- 用于嵌套显示的简化序列化器 ---



class TeamMemberSerializer(serializers.ModelSerializer):
    """用于显示团队成员信息的简化序列化器"""
    is_captain = serializers.SerializerMethodField()
    major_name = serializers.CharField(source='major.major_name', read_only=True)

    class Meta:
        model = Student
        fields = [
            'stu_id', 'stu_no', 'stu_name', 'grade',
            'major_name', 'phone', 'email', 'is_captain'
        ]

    def get_is_captain(self, obj):
        group = self.context.get('group')
        if group:
            return group.captain_id == obj.stu_id
        return hasattr(obj, 'led_group') and obj.led_group is not None


class TeamAdvisorSerializer(serializers.ModelSerializer):
    """用于显示导师信息的简化序列化器"""

    class Meta:
        model = teacher
        fields = [
            'teacher_id',
            'teacher_no',
            'teacher_name',
            'phone',
            'email',
            'research_direction',
            'introduction',
        ]


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
    members = serializers.SerializerMethodField()
    advisor = TeamAdvisorSerializer(read_only=True)
    preferred_advisor_1 = TeamAdvisorSerializer(read_only=True)
    preferred_advisor_2 = TeamAdvisorSerializer(read_only=True)
    preferred_advisor_3 = TeamAdvisorSerializer(read_only=True)
    event_name = serializers.CharField(source='event.event_name', read_only=True)
    event_id = serializers.IntegerField(source='event.event_id', read_only=True)
    member_count = serializers.SerializerMethodField()
    group_member_limit = serializers.IntegerField(source='event.group_member_limit', read_only=True)  # 添加团队人数上限字段

    student_preference_rank = serializers.IntegerField(read_only=True, required=False)
    my_preference_rank = serializers.IntegerField(read_only=True, required=False)

    # ✅ 新增：项目简介截取版本
    project_description_short = serializers.SerializerMethodField()

    class Meta:
        model = Group
        fields = [
            'group_id', 'group_name', 'project_title', 'project_description',
            'project_description_short',  # ✅ 新增
            'event_id', 'event_name', 'captain', 'members', 'member_count',
            'advisor', 'preferred_advisor_1', 'preferred_advisor_2', 'preferred_advisor_3',
            'student_preference_rank',
            'my_preference_rank',
            'group_member_limit'
        ]

    def get_members(self, obj):
        members = obj.members.select_related('major').all()
        # 传递团队信息到上下文，用于判断队长
        return TeamMemberSerializer(
            members,
            many=True,
            context={'group': obj}
        ).data

    def get_member_count(self, obj):
        return obj.members.count()

    def get_project_description_short(self, obj):
        if obj.project_description:
            desc = obj.project_description
            return desc[:100] + ('...' if len(desc) > 100 else '')
        return ''

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
            'preferred_advisor_1_id', 'preferred_advisor_2_id', 'preferred_advisor_3_id',
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

            group_member_limit = active_event.group_member_limit
            if len(self.context.get('member_ids', [])) + 1 > group_member_limit:  # 包括队长
                raise serializers.ValidationError(f"团队成员人数不能超过 {group_member_limit} 人（含队长）。")

        # 2. 验证团队名称唯一性
        group_name = data.get('group_name')
        if group_name:
            query = Group.objects.filter(event=active_event, group_name=group_name)
            if self.instance:
                query = query.exclude(pk=self.instance.pk)
            if query.exists():
                raise serializers.ValidationError(f"团队名称 '{group_name}' 在本次活动中已被使用。")

        return data


class TeacherPreferenceSerializer(serializers.Serializer):
    """
    接收教师提交的志愿列表。
    """
    preferences = serializers.DictField(
        child=serializers.IntegerField(),
        allow_empty=True
    )

    def validate_preferences(self, value):
        if not isinstance(value, dict):
            raise serializers.ValidationError("Preferences 必须是一个字典。")

        # [彻底修复] 从 context 中获取 active_event
        active_event = self.context.get('active_event')
        if not active_event:
            # 这是一个内部错误，正常情况下 context 总应该有 active_event
            raise serializers.ValidationError("验证失败：缺少活动上下文。")

        limit = self.context.get('limit', 5)
        if len(value) > limit:
            raise serializers.ValidationError(f"您最多只能选择 {limit} 个志愿小组。")

        for rank, group_id in value.items():
            try:
                rank_int = int(rank)
                if not (1 <= rank_int <= limit):
                    raise serializers.ValidationError(f"志愿排名 '{rank}' 无效，必须在 1 到 {limit} 之间。")
            except (ValueError, TypeError):
                raise serializers.ValidationError(f"志愿排名 '{rank}' 必须是整数。")

            # [彻底修复] 确保小组不仅存在，而且属于当前活动
            if not Group.objects.filter(pk=group_id, event=active_event).exists():
                raise serializers.ValidationError(f"ID为 {group_id} 的小组不存在或不属于当前活动。")

        if len(set(value.values())) != len(value.values()):
            raise serializers.ValidationError("不能将同一个小组选为多个志愿。")

        return value



class ProvisionalAssignmentSerializer(serializers.ModelSerializer):
    """
    临时分配序列化器
    """
    group = GroupDetailSerializer(read_only=True)
    teacher = TeamAdvisorSerializer(read_only=True)
    event_id = serializers.IntegerField(source='event.event_id', read_only=True)

    class Meta:
        model = ProvisionalAssignment
        fields = [
            'id',  # ✅ 使用 Django 默认的 'id' 字段
            'event_id',
            'group',
            'teacher',
            'assignment_type',
            'score',
            'explanation'
        ]


class GroupListSerializer(serializers.ModelSerializer):
    """
    ✅ 新增：团队列表序列化器
    用于列表显示，只包含关键信息，提高性能
    """
    captain_name = serializers.CharField(source='captain.stu_name', read_only=True)
    advisor_name = serializers.CharField(source='advisor.teacher_name', read_only=True)
    event_name = serializers.CharField(source='event.event_name', read_only=True)
    member_count = serializers.IntegerField(source='members.count', read_only=True)
    project_description_short = serializers.SerializerMethodField()

    class Meta:
        model = Group
        fields = [
            'group_id', 'group_name', 'project_title',
            'project_description_short',
            'event_name', 'captain_name', 'advisor_name', 'member_count'
        ]

    def get_project_description_short(self, obj):
        """项目简介截取"""
        if obj.project_description:
            desc = obj.project_description
            return desc[:50] + ('...' if len(desc) > 50 else '')
        return ''




class AdvisedGroupSummarySerializer(serializers.ModelSerializer):
    """
    教师查看自己指导团队的摘要信息
    """
    captain = TeamMemberSerializer(read_only=True)
    member_count = serializers.IntegerField(source='members.count', read_only=True)
    event_name = serializers.CharField(source='event.event_name', read_only=True)
    event_id = serializers.IntegerField(source='event.event_id', read_only=True)
    project_description_short = serializers.SerializerMethodField()
    group_member_limit = serializers.IntegerField(source='event.group_member_limit', read_only=True)  # 添加团队人数上限字段

    class Meta:
        model = Group
        fields = [
            'group_id', 'group_name', 'project_title',
            'project_description_short',
            'event_id', 'event_name', 'captain', 'member_count',
            'group_member_limit'
        ]

    def get_project_description_short(self, obj):
        if obj.project_description:
            desc = obj.project_description
            return desc[:100] + ('...' if len(desc) > 100 else '')
        return ''
