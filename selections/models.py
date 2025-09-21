from django.db import models
from django.conf import settings
from django.core.exceptions import ValidationError


class MentorSelection(models.Model):
    """Student/Team mentor selection model"""
    
    SELECTION_STATUS = [
        ('pending', '待审核'),
        ('approved', '已通过'),
        ('rejected', '已拒绝'),
        ('cancelled', '已取消'),
    ]
    
    SELECTION_TYPE = [
        ('individual', '个人'),
        ('team', '团队'),
    ]
    
    student = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='mentor_selections',
        null=True,
        blank=True,
        verbose_name='学生'
    )
    
    team = models.ForeignKey(
        'teams.Team',
        on_delete=models.CASCADE,
        related_name='mentor_selections',
        null=True,
        blank=True,
        verbose_name='团队'
    )
    
    teacher = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='student_selections',
        verbose_name='导师'
    )
    
    selection_type = models.CharField(
        max_length=10,
        choices=SELECTION_TYPE,
        verbose_name='选择类型'
    )
    
    status = models.CharField(
        max_length=10,
        choices=SELECTION_STATUS,
        default='pending',
        verbose_name='状态'
    )
    
    priority = models.PositiveIntegerField(
        default=1,
        verbose_name='优先级'
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
        verbose_name = '导师选择'
        verbose_name_plural = '导师选择'
        db_table = 'selections_mentor_selection'
        ordering = ['-applied_at']
    
    def clean(self):
        # 确保学生或团队二选一
        if not self.student and not self.team:
            raise ValidationError('必须指定学生或团队')
        if self.student and self.team:
            raise ValidationError('不能同时指定学生和团队')
        
        # 验证选择类型与实际对象匹配
        if self.selection_type == 'individual' and not self.student:
            raise ValidationError('个人选择必须指定学生')
        if self.selection_type == 'team' and not self.team:
            raise ValidationError('团队选择必须指定团队')
        
        # 验证导师角色
        if self.teacher and not self.teacher.is_teacher:
            raise ValidationError('选择的用户不是导师')
    
    def save(self, *args, **kwargs):
        # 根据实际对象设置选择类型
        if self.student and not self.team:
            self.selection_type = 'individual'
        elif self.team and not self.student:
            self.selection_type = 'team'
        
        self.clean()
        super().save(*args, **kwargs)
    
    def __str__(self):
        applicant = self.team.name if self.team else (self.student.real_name or self.student.username)
        teacher_name = self.teacher.real_name or self.teacher.username
        return f"{applicant} 选择导师 {teacher_name} ({self.get_status_display()})"
    
    @property
    def applicant_name(self):
        if self.team:
            return self.team.name
        return self.student.real_name or self.student.username


class TeacherSelection(models.Model):
    """Teacher selection of students/teams"""
    
    SELECTION_STATUS = [
        ('interested', '感兴趣'),
        ('selected', '已选择'),
        ('rejected', '已拒绝'),
    ]
    
    teacher = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='teacher_student_selections',
        verbose_name='导师'
    )
    
    student = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='teacher_selections',
        null=True,
        blank=True,
        verbose_name='学生'
    )
    
    team = models.ForeignKey(
        'teams.Team',
        on_delete=models.CASCADE,
        related_name='teacher_selections',
        null=True,
        blank=True,
        verbose_name='团队'
    )
    
    status = models.CharField(
        max_length=10,
        choices=SELECTION_STATUS,
        default='interested',
        verbose_name='状态'
    )
    
    message = models.TextField(
        blank=True,
        verbose_name='留言'
    )
    
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新时间')
    
    class Meta:
        verbose_name = '导师选择学生'
        verbose_name_plural = '导师选择学生'
        db_table = 'selections_teacher_selection'
        ordering = ['-created_at']
    
    def clean(self):
        # 确保学生或团队二选一
        if not self.student and not self.team:
            raise ValidationError('必须指定学生或团队')
        if self.student and self.team:
            raise ValidationError('不能同时指定学生和团队')
        
        # 验证导师角色
        if self.teacher and not self.teacher.is_teacher:
            raise ValidationError('用户不是导师')
    
    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)
    
    def __str__(self):
        target = self.team.name if self.team else (self.student.real_name or self.student.username)
        teacher_name = self.teacher.real_name or self.teacher.username
        return f"导师 {teacher_name} 选择 {target} ({self.get_status_display()})"


class SelectionPeriod(models.Model):
    """Selection period management"""
    
    name = models.CharField(
        max_length=100,
        verbose_name='选择周期名称'
    )
    
    description = models.TextField(
        blank=True,
        verbose_name='描述'
    )
    
    student_selection_start = models.DateTimeField(
        verbose_name='学生选择开始时间'
    )
    
    student_selection_end = models.DateTimeField(
        verbose_name='学生选择结束时间'
    )
    
    teacher_selection_start = models.DateTimeField(
        verbose_name='导师选择开始时间'
    )
    
    teacher_selection_end = models.DateTimeField(
        verbose_name='导师选择结束时间'
    )
    
    is_active = models.BooleanField(
        default=True,
        verbose_name='是否活跃'
    )
    
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新时间')
    
    class Meta:
        verbose_name = '选择周期'
        verbose_name_plural = '选择周期'
        db_table = 'selections_selection_period'
        ordering = ['-created_at']
    
    def __str__(self):
        return self.name
    
    def clean(self):
        # 验证时间逻辑
        if self.student_selection_start >= self.student_selection_end:
            raise ValidationError('学生选择开始时间必须早于结束时间')
        if self.teacher_selection_start >= self.teacher_selection_end:
            raise ValidationError('导师选择开始时间必须早于结束时间')
    
    @property
    def is_student_selection_active(self):
        from django.utils import timezone
        now = timezone.now()
        return (self.is_active and 
                self.student_selection_start <= now <= self.student_selection_end)
    
    @property
    def is_teacher_selection_active(self):
        from django.utils import timezone
        now = timezone.now()
        return (self.is_active and 
                self.teacher_selection_start <= now <= self.teacher_selection_end)
