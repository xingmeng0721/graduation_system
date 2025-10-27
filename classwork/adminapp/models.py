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
    event_name = models.CharField(max_length=255, verbose_name='互选活动名称')
    start_time = models.DateTimeField(verbose_name='开始时间')
    end_time = models.DateTimeField(verbose_name='截止时间')

    # 参与互选的教师和学生
    teachers = models.ManyToManyField(teacher, related_name='mutual_selection_events', verbose_name='参与教师')
    students = models.ManyToManyField(Student, related_name='mutual_selection_events', verbose_name='参与学生')

    class Meta:
        db_table = 'mutual_selection_event'
        verbose_name = '互选活动'
        verbose_name_plural = verbose_name

    def __str__(self):
        return self.event_name