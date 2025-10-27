from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
# from adminapp.models import MutualSelectionEvent
# from teacherapp.models import teacher

# 专业模型
class Major(models.Model):
    major_id = models.AutoField(primary_key=True)
    major_name = models.CharField(max_length=255, unique=True, verbose_name='专业名称')

    class Meta:
        db_table = 'major'
        verbose_name = '专业'
        verbose_name_plural = verbose_name

    def __str__(self):
        return self.major_name


class StudentManager(BaseUserManager):
    def create_user(self, stu_no, password=None, **extra_fields):
        if not stu_no:
            raise ValueError('学号是必填项')
        user = self.model(stu_no=stu_no, **extra_fields)
        user.set_password(password) # 自动处理密码哈希
        user.save(using=self._db)
        return user

# 学生模型
class Student(AbstractBaseUser):
    stu_id = models.AutoField(primary_key=True)
    stu_no = models.CharField(max_length=50, unique=True, verbose_name='学号')
    stu_name = models.CharField(max_length=255, verbose_name='姓名')
    grade = models.CharField(max_length=50, verbose_name='年级')
    phone = models.CharField(max_length=20, blank=True, null=True, verbose_name='手机号')
    # is_gleader = models.BooleanField(default=False, verbose_name='是否为组长')
    email = models.EmailField(max_length=255, blank=True, null=True, verbose_name='电子邮箱')

    # 外键关系
    major = models.ForeignKey(Major, on_delete=models.SET_NULL, null=True, blank=True, related_name='students', verbose_name='专业')
    # group = models.ForeignKey(Group, on_delete=models.SET_NULL, null=True, blank=True, related_name='students', verbose_name='分组')

    # Django认证系统需要的字段
    is_staff = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)

    objects = StudentManager()

    USERNAME_FIELD = 'stu_no'
    REQUIRED_FIELDS = ['stu_name', 'grade']

    class Meta:
        db_table = 'student'
        verbose_name = '学生'
        verbose_name_plural = verbose_name

    def __str__(self):
        return self.stu_name

from django.utils import timezone
from datetime import timedelta

class EmailVerifyCode(models.Model):
    email = models.EmailField(verbose_name='邮箱')
    code = models.CharField(max_length=6, verbose_name='验证码')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'email_verify_code'
        verbose_name = '邮箱验证码'
        verbose_name_plural = verbose_name

    def is_expired(self):
        """验证码10分钟内有效"""
        return timezone.now() > self.created_at + timedelta(minutes=10)

    def __str__(self):
        return f"{self.email}-{self.code}"


# class Group(models.Model):
#     group_id = models.AutoField(primary_key=True)
#     group_name = models.CharField(max_length=255, verbose_name='分组名称')
#
#     # 关联到互选活动，允许为空以保证其他功能可用
#     event = models.ForeignKey(
#         MutualSelectionEvent,
#         on_delete=models.CASCADE,
#         related_name='groups',
#         verbose_name='所属互选活动',
#         null=True,
#         blank=True
#     )
#
#     # 直接关联指导老师
#     advisor = models.ForeignKey(
#         teacher,
#         on_delete=models.SET_NULL,
#         related_name='advised_groups',
#         verbose_name='指导老师',
#         null=True,
#         blank=True
#     )
#
#     # 显式定义队长，确保唯一性
#     captain = models.OneToOneField(
#         Student,
#         on_delete=models.SET_NULL,
#         related_name='led_group',
#         verbose_name='队长',
#         null=True,
#         blank=True
#     )
#
#     # 通过 GroupMembership 反向关联所有成员
#     members = models.ManyToManyField(
#         Student,
#         through='GroupMembership',
#         related_name='member_of_groups'
#     )
#
#     class Meta:
#         db_table = 'group'
#         verbose_name = '分组'
#         verbose_name_plural = verbose_name
#         unique_together = ('event', 'group_name')  # 同一个活动下的分组名称必须唯一
#
#     def clean(self):
#         # 验证1: 队长的指导老师必须和小组的指导老师是同一人 (如果都已设置)
#         if self.captain and self.advisor:
#             # 假设你已经有了 Assignment 模型来记录最终分配结果
#             try:
#                 assignment = self.captain.assignment
#                 if assignment.teacher != self.advisor:
#                     raise ValidationError(
#                         f"队长 {self.captain.stu_name} 的导师不是 {self.advisor.teacher_name}，不能设置为该组的指导老师。")
#             except Student.assignment.RelatedObjectDoesNotExist:
#                 # 如果还没有最终分配结果，可以暂时跳过此验证或采取其他逻辑
#                 pass
#
#         # 验证2: 队长必须是小组成员之一
#         if self.captain and not self.members.filter(pk=self.captain.pk).exists():
#             raise ValidationError("队长必须是小组成员。")
#
#     def __str__(self):
#         return self.group_name
#
# class GroupMembership(models.Model):
#     """
#     这个中间模型清晰地定义了学生和团队的关系。
#     一个学生只能是一个团队的成员。
#     """
#     student = models.OneToOneField(
#         Student,
#         on_delete=models.CASCADE,
#         primary_key=True, # 将学生作为主键，天然保证一个学生只能加入一个组
#         related_name='membership'
#     )
#     group = models.ForeignKey(Group, on_delete=models.CASCADE, related_name='memberships')
#     date_joined = models.DateTimeField(auto_now_add=True)
#
#     class Meta:
#         db_table = 'group_membership'
#         verbose_name = '团队成员关系'
#         verbose_name_plural = verbose_name
