from django.db import models
from studentapp.models import Student, Major
from teacherapp.models import teacher

# Create your models here.
class AdminUser(models.Model):
    #主键
    admin_id = models.AutoField(primary_key=True)
    admin_name = models.CharField(max_length=150, unique=True)
    admin_username = models.CharField(max_length=150, unique=True)
    admin_password = models.CharField(max_length=128)

    def __str__(self):
        return self.admin_username


class MutualSelectionEvent(models.Model):
    event_id = models.AutoField(primary_key=True)
    event_name = models.CharField(max_length=255, verbose_name='分组名称')
    stu_start_time = models.DateTimeField(verbose_name='学生开始时间')
    stu_end_time = models.DateTimeField(verbose_name='学生截止时间')
    tea_start_time = models.DateTimeField(verbose_name='教师开始时间')
    tea_end_time = models.DateTimeField(verbose_name='教师截止时间')
    teacher_choice_limit = models.PositiveIntegerField(
        default=5,
        verbose_name='教师可选小组数',
        help_text='每个导师在此活动中最多可以选择的小组数量'
    )

    # 参与互选的教师和学生
    teachers = models.ManyToManyField(teacher, related_name='mutual_selection_events', verbose_name='参与教师')
    students = models.ManyToManyField(Student, related_name='mutual_selection_events', verbose_name='参与学生')

    class Meta:
        db_table = 'mutual_selection_event'
        verbose_name = '毕业设置分组配置'
        verbose_name_plural = verbose_name

    def __str__(self):
        return self.event_name