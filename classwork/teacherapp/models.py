from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin


class TeacherManager(BaseUserManager):
    def create_user(self, teacher_no, password=None, **extra_fields):
        """
        创建并保存一个普通教师用户。
        """
        if not teacher_no:
            raise ValueError('教师工号是必填项')
        if 'teacher_name' not in extra_fields:
            raise ValueError('姓名字段是必填项')

        # 创建用户实例
        user = self.model(teacher_no=teacher_no, **extra_fields)
        # 设置并加密密码
        user.set_password(password)
        user.save(using=self._db)
        return user


# 教师模型
class teacher(AbstractBaseUser):
    teacher_id = models.AutoField(primary_key=True)
    teacher_no = models.CharField(max_length=50, unique=True, verbose_name='工号')
    teacher_name = models.CharField(max_length=255, verbose_name='姓名')
    phone = models.CharField(max_length=20, blank=True, null=True, verbose_name='手机号')
    email = models.EmailField(max_length=255, blank=True, null=True, verbose_name='电子邮箱')
    research_direction = models.CharField(max_length=255, blank=True, null=True, verbose_name='研究方向')
    introduction = models.TextField(blank=True, null=True, verbose_name='简介')



    # Django认证系统需要的字段
    is_staff = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    objects = TeacherManager()


    USERNAME_FIELD = 'teacher_no'
    REQUIRED_FIELDS = ['teacher_name']

    class Meta:
        db_table = 'teacher'
        verbose_name = '教师'
        verbose_name_plural = verbose_name

    def __str__(self):
        return self.teacher_name