from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import Team, TeamMembership, TeamInvitation
from accounts.serializers import UserSerializer

User = get_user_model()


class TeamMembershipSerializer(serializers.ModelSerializer):
    """团队成员资格序列化器"""
    student = UserSerializer(read_only=True)
    student_name = serializers.SerializerMethodField()
    
    class Meta:
        model = TeamMembership
        fields = ['id', 'student', 'student_name', 'status', 'role',
                 'application_message', 'response_message',
                 'applied_at', 'processed_at']
        read_only_fields = ['applied_at']
    
    def get_student_name(self, obj):
        return obj.student.real_name or obj.student.username


class TeamSerializer(serializers.ModelSerializer):
    """团队序列化器"""
    leader = UserSerializer(read_only=True)
    leader_name = serializers.SerializerMethodField()
    current_member_count = serializers.ReadOnlyField()
    can_add_members = serializers.ReadOnlyField()
    memberships = TeamMembershipSerializer(many=True, read_only=True)
    
    class Meta:
        model = Team
        fields = ['id', 'name', 'description', 'project_title', 'project_description',
                 'leader', 'leader_name', 'max_members', 'current_member_count',
                 'can_add_members', 'status', 'is_public', 'created_at',
                 'updated_at', 'memberships']
        read_only_fields = ['leader', 'created_at', 'updated_at', 'current_member_count']
    
    def get_leader_name(self, obj):
        return obj.leader.real_name or obj.leader.username


class TeamCreateSerializer(serializers.ModelSerializer):
    """团队创建序列化器"""
    
    class Meta:
        model = Team
        fields = ['name', 'description', 'project_title', 'project_description',
                 'max_members', 'is_public']
    
    def create(self, validated_data):
        request = self.context['request']
        validated_data['leader'] = request.user
        team = super().create(validated_data)
        
        # 创建队长的成员资格记录
        TeamMembership.objects.create(
            team=team,
            student=request.user,
            status='approved',
            role='队长'
        )
        return team


class TeamListSerializer(serializers.ModelSerializer):
    """团队列表序列化器"""
    leader_name = serializers.SerializerMethodField()
    current_member_count = serializers.ReadOnlyField()
    
    class Meta:
        model = Team
        fields = ['id', 'name', 'description', 'project_title',
                 'leader_name', 'max_members', 'current_member_count',
                 'status', 'is_public', 'created_at']
    
    def get_leader_name(self, obj):
        return obj.leader.real_name or obj.leader.username


class TeamMembershipCreateSerializer(serializers.ModelSerializer):
    """团队成员申请序列化器"""
    
    class Meta:
        model = TeamMembership
        fields = ['team', 'application_message']
    
    def create(self, validated_data):
        request = self.context['request']
        validated_data['student'] = request.user
        return super().create(validated_data)
    
    def validate_team(self, value):
        request = self.context['request']
        
        # 检查是否已经是成员
        if value.is_member(request.user):
            raise serializers.ValidationError("您已经是该团队的成员")
        
        # 检查是否已有待审核申请
        if TeamMembership.objects.filter(
            team=value, student=request.user, status='pending'
        ).exists():
            raise serializers.ValidationError("您已有待审核的申请")
        
        # 检查团队是否可以添加成员
        if not value.can_add_members:
            raise serializers.ValidationError("该团队当前不接受新成员")
        
        return value


class TeamMembershipUpdateSerializer(serializers.ModelSerializer):
    """团队成员资格更新序列化器"""
    
    class Meta:
        model = TeamMembership
        fields = ['status', 'role', 'response_message']


class TeamInvitationSerializer(serializers.ModelSerializer):
    """团队邀请序列化器"""
    team = TeamListSerializer(read_only=True)
    inviter = UserSerializer(read_only=True)
    invitee = UserSerializer(read_only=True)
    inviter_name = serializers.SerializerMethodField()
    invitee_name = serializers.SerializerMethodField()
    is_expired = serializers.ReadOnlyField()
    
    class Meta:
        model = TeamInvitation
        fields = ['id', 'team', 'inviter', 'inviter_name', 'invitee', 'invitee_name',
                 'message', 'status', 'created_at', 'responded_at',
                 'expires_at', 'is_expired']
        read_only_fields = ['inviter', 'created_at']
    
    def get_inviter_name(self, obj):
        return obj.inviter.real_name or obj.inviter.username
    
    def get_invitee_name(self, obj):
        return obj.invitee.real_name or obj.invitee.username


class TeamInvitationCreateSerializer(serializers.ModelSerializer):
    """团队邀请创建序列化器"""
    
    class Meta:
        model = TeamInvitation
        fields = ['team', 'invitee', 'message', 'expires_at']
    
    def create(self, validated_data):
        request = self.context['request']
        validated_data['inviter'] = request.user
        return super().create(validated_data)
    
    def validate(self, attrs):
        request = self.context['request']
        team = attrs['team']
        invitee = attrs['invitee']
        
        # 检查是否是团队领导或成员
        if not (team.is_leader(request.user) or team.is_member(request.user)):
            raise serializers.ValidationError("只有团队成员可以发出邀请")
        
        # 检查被邀请人是否已经是成员
        if team.is_member(invitee):
            raise serializers.ValidationError("该用户已经是团队成员")
        
        # 检查是否已有待处理邀请
        if TeamInvitation.objects.filter(
            team=team, invitee=invitee, status='pending'
        ).exists():
            raise serializers.ValidationError("已有待处理的邀请")
        
        # 检查团队是否可以添加成员
        if not team.can_add_members:
            raise serializers.ValidationError("团队当前不接受新成员")
        
        return attrs