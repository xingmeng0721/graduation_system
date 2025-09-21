from django.db import models
from django.conf import settings
from django.core.validators import MinLengthValidator


class Team(models.Model):
    """Student team model"""
    
    TEAM_STATUS = [
        ('forming', '组建中'),
        ('complete', '已完成'),
        ('disbanded', '已解散'),
    ]
    
    name = models.CharField(
        max_length=100,
        unique=True,
        validators=[MinLengthValidator(2)],
        verbose_name='团队名称'
    )
    
    description = models.TextField(
        blank=True,
        verbose_name='团队描述'
    )
    
    project_title = models.CharField(
        max_length=200,
        blank=True,
        verbose_name='项目标题'
    )
    
    project_description = models.TextField(
        blank=True,
        verbose_name='项目描述'
    )
    
    leader = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='led_teams',
        verbose_name='队长'
    )
    
    members = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        through='TeamMembership',
        related_name='teams',
        verbose_name='团队成员'
    )
    
    max_members = models.PositiveIntegerField(
        default=4,
        verbose_name='最大成员数'
    )
    
    status = models.CharField(
        max_length=10,
        choices=TEAM_STATUS,
        default='forming',
        verbose_name='团队状态'
    )
    
    is_public = models.BooleanField(
        default=True,
        verbose_name='是否公开'
    )
    
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新时间')
    
    class Meta:
        verbose_name = '团队'
        verbose_name_plural = '团队'
        db_table = 'teams_team'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.name} (队长: {self.leader.real_name or self.leader.username})"
    
    @property
    def current_member_count(self):
        return self.memberships.filter(status='approved').count()
    
    @property
    def can_add_members(self):
        return self.current_member_count < self.max_members and self.status == 'forming'
    
    def is_member(self, user):
        return self.memberships.filter(
            student=user,
            status='approved'
        ).exists()
    
    def is_leader(self, user):
        return self.leader == user


class TeamMembership(models.Model):
    """Team membership model with approval system"""
    
    MEMBERSHIP_STATUS = [
        ('pending', '待审核'),
        ('approved', '已通过'),
        ('rejected', '已拒绝'),
        ('left', '已退出'),
    ]
    
    team = models.ForeignKey(
        Team,
        on_delete=models.CASCADE,
        related_name='memberships',
        verbose_name='团队'
    )
    
    student = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='memberships',
        verbose_name='学生'
    )
    
    status = models.CharField(
        max_length=10,
        choices=MEMBERSHIP_STATUS,
        default='pending',
        verbose_name='状态'
    )
    
    role = models.CharField(
        max_length=50,
        blank=True,
        verbose_name='团队角色'
    )
    
    application_message = models.TextField(
        blank=True,
        verbose_name='申请信息'
    )
    
    response_message = models.TextField(
        blank=True,
        verbose_name='回复信息'
    )
    
    applied_at = models.DateTimeField(auto_now_add=True, verbose_name='申请时间')
    processed_at = models.DateTimeField(null=True, blank=True, verbose_name='处理时间')
    
    class Meta:
        verbose_name = '团队成员资格'
        verbose_name_plural = '团队成员资格'
        db_table = 'teams_membership'
        unique_together = [('team', 'student')]
        ordering = ['-applied_at']
    
    def __str__(self):
        return f"{self.student.real_name or self.student.username} - {self.team.name} ({self.get_status_display()})"


class TeamInvitation(models.Model):
    """Team invitation model"""
    
    INVITATION_STATUS = [
        ('pending', '待回应'),
        ('accepted', '已接受'),
        ('declined', '已拒绝'),
        ('expired', '已过期'),
    ]
    
    team = models.ForeignKey(
        Team,
        on_delete=models.CASCADE,
        related_name='invitations',
        verbose_name='团队'
    )
    
    inviter = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='sent_invitations',
        verbose_name='邀请人'
    )
    
    invitee = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='received_invitations',
        verbose_name='被邀请人'
    )
    
    message = models.TextField(
        blank=True,
        verbose_name='邀请信息'
    )
    
    status = models.CharField(
        max_length=10,
        choices=INVITATION_STATUS,
        default='pending',
        verbose_name='状态'
    )
    
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    responded_at = models.DateTimeField(null=True, blank=True, verbose_name='回应时间')
    expires_at = models.DateTimeField(verbose_name='过期时间')
    
    class Meta:
        verbose_name = '团队邀请'
        verbose_name_plural = '团队邀请'
        db_table = 'teams_invitation'
        unique_together = [('team', 'invitee')]
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.team.name} 邀请 {self.invitee.real_name or self.invitee.username}"
    
    @property
    def is_expired(self):
        from django.utils import timezone
        return timezone.now() > self.expires_at
