from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager


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
    email = models.EmailField(max_length=255, blank=True, null=True, verbose_name='电子邮箱')
    internship_location = models.CharField(max_length=255,blank=True,null=True,verbose_name="实习地点")

    # 外键关系
    major = models.ForeignKey(Major, on_delete=models.SET_NULL, null=True, blank=True, related_name='students', verbose_name='专业')

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
