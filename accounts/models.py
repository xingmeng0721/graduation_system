from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.validators import RegexValidator


class User(AbstractUser):
    """Extended user model with role support"""
    
    USER_ROLES = [
        ('student', '学生'),
        ('teacher', '教师'),
        ('admin', '管理员'),
    ]
    
    role = models.CharField(
        max_length=10,
        choices=USER_ROLES,
        default='student',
        verbose_name='角色'
    )
    
    phone_regex = RegexValidator(
        regex=r'^\+?1?\d{9,15}$',
        message="电话号码格式: '+999999999'. 最多15位数字."
    )
    phone_number = models.CharField(
        validators=[phone_regex],
        max_length=17,
        blank=True,
        verbose_name='电话号码'
    )
    
    real_name = models.CharField(
        max_length=50,
        blank=True,
        verbose_name='真实姓名'
    )
    
    student_id = models.CharField(
        max_length=20,
        blank=True,
        unique=True,
        null=True,
        verbose_name='学号/工号'
    )
    
    department = models.CharField(
        max_length=100,
        blank=True,
        verbose_name='院系'
    )
    
    major = models.CharField(
        max_length=100,
        blank=True,
        verbose_name='专业'
    )
    
    grade = models.CharField(
        max_length=10,
        blank=True,
        verbose_name='年级'
    )
    
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新时间')
    
    class Meta:
        verbose_name = '用户'
        verbose_name_plural = '用户'
        db_table = 'accounts_user'
    
    def __str__(self):
        return f"{self.real_name or self.username} ({self.get_role_display()})"
    
    @property
    def is_student(self):
        return self.role == 'student'
    
    @property
    def is_teacher(self):
        return self.role == 'teacher'
    
    @property
    def is_admin_user(self):
        return self.role == 'admin'


class StudentProfile(models.Model):
    """Student extended profile"""
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='student_profile',
        verbose_name='用户'
    )
    
    gpa = models.FloatField(
        null=True,
        blank=True,
        verbose_name='GPA'
    )
    
    research_interests = models.TextField(
        blank=True,
        verbose_name='研究兴趣'
    )
    
    skills = models.TextField(
        blank=True,
        verbose_name='技能'
    )
    
    introduction = models.TextField(
        blank=True,
        verbose_name='自我介绍'
    )
    
    class Meta:
        verbose_name = '学生档案'
        verbose_name_plural = '学生档案'
        db_table = 'accounts_student_profile'
    
    def __str__(self):
        return f"{self.user.real_name or self.user.username}的学生档案"


class TeacherProfile(models.Model):
    """Teacher extended profile"""
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='teacher_profile',
        verbose_name='用户'
    )
    
    title = models.CharField(
        max_length=50,
        blank=True,
        verbose_name='职称'
    )
    
    research_areas = models.TextField(
        blank=True,
        verbose_name='研究领域'
    )
    
    max_students = models.PositiveIntegerField(
        default=5,
        verbose_name='最大指导学生数'
    )
    
    current_students = models.PositiveIntegerField(
        default=0,
        verbose_name='当前指导学生数'
    )
    
    introduction = models.TextField(
        blank=True,
        verbose_name='导师介绍'
    )
    
    requirements = models.TextField(
        blank=True,
        verbose_name='对学生要求'
    )
    
    is_accepting = models.BooleanField(
        default=True,
        verbose_name='是否接收新学生'
    )
    
    class Meta:
        verbose_name = '教师档案'
        verbose_name_plural = '教师档案'
        db_table = 'accounts_teacher_profile'
    
    def __str__(self):
        return f"{self.user.real_name or self.user.username}的教师档案"
    
    @property
    def can_accept_more_students(self):
        return self.is_accepting and self.current_students < self.max_students
