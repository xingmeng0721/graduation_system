from rest_framework import serializers
from .models import Group, GroupMembership
from studentapp.models import Student
from teacherapp.models import teacher

class TeamMemberSerializer(serializers.ModelSerializer):
    """用于显示团队成员信息的简化序列化器"""
    class Meta:
        model = Student
        fields = ['stu_id', 'stu_no', 'stu_name']

class TeamAdvisorSerializer(serializers.ModelSerializer):
    """用于显示导师信息的简化序列化器"""
    class Meta:
        model = teacher
        fields = ['teacher_id', 'teacher_no', 'teacher_name']

class GroupDetailSerializer(serializers.ModelSerializer):
    """用于显示团队完整信息的序列化器"""
    captain = TeamMemberSerializer(read_only=True)
    members = TeamMemberSerializer(many=True, read_only=True)
    advisor = TeamAdvisorSerializer(read_only=True)
    preferred_advisor_1 = TeamAdvisorSerializer(read_only=True)
    preferred_advisor_2 = TeamAdvisorSerializer(read_only=True)
    preferred_advisor_3 = TeamAdvisorSerializer(read_only=True)
    event_name = serializers.CharField(source='event.event_name', read_only=True)

    class Meta:
        model = Group
        fields = [
            'group_id', 'group_name', 'event_name', 'captain', 'members',
            'advisor', 'preferred_advisor_1', 'preferred_advisor_2', 'preferred_advisor_3'
        ]

class GroupCreateSerializer(serializers.ModelSerializer):
    """用于创建新团队的序列化器"""
    class Meta:
        model = Group
        fields = ['group_name', 'preferred_advisor_1', 'preferred_advisor_2', 'preferred_advisor_3']