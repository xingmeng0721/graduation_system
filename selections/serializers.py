from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import MentorSelection, TeacherSelection, SelectionPeriod
from accounts.serializers import UserSerializer, TeacherListSerializer
from teams.serializers import TeamListSerializer

User = get_user_model()


class MentorSelectionSerializer(serializers.ModelSerializer):
    """导师选择序列化器"""
    student = UserSerializer(read_only=True)
    team = TeamListSerializer(read_only=True)
    teacher = TeacherListSerializer(read_only=True)
    applicant_name = serializers.ReadOnlyField()
    
    class Meta:
        model = MentorSelection
        fields = ['id', 'student', 'team', 'teacher', 'applicant_name',
                 'selection_type', 'status', 'priority',
                 'application_message', 'response_message',
                 'applied_at', 'processed_at']
        read_only_fields = ['student', 'team', 'selection_type', 'applied_at']


class MentorSelectionCreateSerializer(serializers.ModelSerializer):
    """导师选择创建序列化器"""
    
    class Meta:
        model = MentorSelection
        fields = ['teacher', 'team', 'priority', 'application_message']
    
    def create(self, validated_data):
        request = self.context['request']
        user = request.user
        
        # 根据用户类型设置学生或团队
        if user.is_student:
            validated_data['student'] = user
            validated_data['selection_type'] = 'individual'
        
        return super().create(validated_data)
    
    def validate_teacher(self, value):
        if not value.is_teacher:
            raise serializers.ValidationError("选择的用户不是导师")
        
        # 检查导师是否接受新学生
        if hasattr(value, 'teacher_profile') and not value.teacher_profile.can_accept_more_students:
            raise serializers.ValidationError("该导师当前不接受新学生")
        
        return value
    
    def validate(self, attrs):
        request = self.context['request']
        teacher = attrs['teacher']
        team = attrs.get('team')
        
        # 检查是否已有相同选择
        if team:
            # 团队选择
            if not team.is_leader(request.user):
                raise serializers.ValidationError("只有队长可以为团队选择导师")
            
            if MentorSelection.objects.filter(
                team=team, teacher=teacher, status='pending'
            ).exists():
                raise serializers.ValidationError("该团队已对此导师有待审核的选择")
        else:
            # 个人选择
            if MentorSelection.objects.filter(
                student=request.user, teacher=teacher, status='pending'
            ).exists():
                raise serializers.ValidationError("您已对此导师有待审核的选择")
        
        return attrs


class MentorSelectionUpdateSerializer(serializers.ModelSerializer):
    """导师选择更新序列化器（用于导师回应）"""
    
    class Meta:
        model = MentorSelection
        fields = ['status', 'response_message']
    
    def validate_status(self, value):
        if value not in ['approved', 'rejected']:
            raise serializers.ValidationError("状态必须是 approved 或 rejected")
        return value


class TeacherSelectionSerializer(serializers.ModelSerializer):
    """导师选择学生序列化器"""
    teacher = TeacherListSerializer(read_only=True)
    student = UserSerializer(read_only=True)
    team = TeamListSerializer(read_only=True)
    
    class Meta:
        model = TeacherSelection
        fields = ['id', 'teacher', 'student', 'team', 'status', 'message',
                 'created_at', 'updated_at']
        read_only_fields = ['teacher', 'created_at', 'updated_at']


class TeacherSelectionCreateSerializer(serializers.ModelSerializer):
    """导师选择学生创建序列化器"""
    
    class Meta:
        model = TeacherSelection
        fields = ['student', 'team', 'message']
    
    def create(self, validated_data):
        request = self.context['request']
        validated_data['teacher'] = request.user
        return super().create(validated_data)
    
    def validate(self, attrs):
        student = attrs.get('student')
        team = attrs.get('team')
        
        # 确保选择了学生或团队，但不能同时选择
        if not student and not team:
            raise serializers.ValidationError("必须选择学生或团队")
        if student and team:
            raise serializers.ValidationError("不能同时选择学生和团队")
        
        # 验证学生角色
        if student and not student.is_student:
            raise serializers.ValidationError("选择的用户不是学生")
        
        request = self.context['request']
        # 检查是否已有相同选择
        filters = {'teacher': request.user}
        if student:
            filters['student'] = student
        else:
            filters['team'] = team
        
        if TeacherSelection.objects.filter(**filters).exists():
            target = student.real_name if student else team.name
            raise serializers.ValidationError(f"您已选择过 {target}")
        
        return attrs


class SelectionPeriodSerializer(serializers.ModelSerializer):
    """选择周期序列化器"""
    is_student_selection_active = serializers.ReadOnlyField()
    is_teacher_selection_active = serializers.ReadOnlyField()
    
    class Meta:
        model = SelectionPeriod
        fields = ['id', 'name', 'description',
                 'student_selection_start', 'student_selection_end',
                 'teacher_selection_start', 'teacher_selection_end',
                 'is_active', 'is_student_selection_active',
                 'is_teacher_selection_active', 'created_at', 'updated_at']
        read_only_fields = ['created_at', 'updated_at']


class MySelectionStatusSerializer(serializers.Serializer):
    """我的选择状态序列化器"""
    has_mentor = serializers.BooleanField()
    mentor_selections = MentorSelectionSerializer(many=True)
    received_teacher_selections = TeacherSelectionSerializer(many=True)
    team_mentor_selection = MentorSelectionSerializer(allow_null=True)


class StatisticsSerializer(serializers.Serializer):
    """统计信息序列化器"""
    total_students = serializers.IntegerField()
    total_teachers = serializers.IntegerField()
    total_teams = serializers.IntegerField()
    total_mentor_selections = serializers.IntegerField()
    pending_mentor_selections = serializers.IntegerField()
    approved_mentor_selections = serializers.IntegerField()
    students_with_mentor = serializers.IntegerField()
    students_without_mentor = serializers.IntegerField()