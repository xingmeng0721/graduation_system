from django.db import models
from django.core.exceptions import ValidationError


class Group(models.Model):
    """
    增强版的分组/团队模型
    """
    group_id = models.AutoField(primary_key=True)
    group_name = models.CharField(max_length=255, verbose_name='分组名称')
    project_title = models.CharField(max_length=255, verbose_name="项目标题", blank=True)
    project_description = models.TextField(verbose_name="项目简介", blank=True)

    # 关联到互选活动，允许为空，以保证在没有活动时其他功能也能正常使用
    event = models.ForeignKey(
        'adminapp.MutualSelectionEvent',
        on_delete=models.CASCADE,
        related_name='groups',
        verbose_name='所属互选活动',
        null=True,
        blank=True
    )
    preferred_advisor_1 = models.ForeignKey(
        'teacherapp.teacher',
        on_delete=models.SET_NULL,
        related_name='preferred_as_first',
        verbose_name='第一志愿导师',
        null=True, blank=True
    )
    preferred_advisor_2 = models.ForeignKey(
        'teacherapp.teacher',
        on_delete=models.SET_NULL,
        related_name='preferred_as_second',
        verbose_name='第二志愿导师',
        null=True, blank=True
    )
    preferred_advisor_3 = models.ForeignKey(
        'teacherapp.teacher',
        on_delete=models.SET_NULL,
        related_name='preferred_as_third',
        verbose_name='第三志愿导师',
        null=True, blank=True
    )

    # 直接关联指导老师
    advisor = models.ForeignKey(
        'teacherapp.teacher',
        on_delete=models.SET_NULL,
        related_name='advised_groups',
        verbose_name='最终指导老师',
        null=True,
        blank=True
    )

    # 显式定义队长，通过 OneToOneField 确保唯一性
    captain = models.OneToOneField(
        'studentapp.Student',
        on_delete=models.SET_NULL,
        related_name='led_group',
        verbose_name='队长',
        null=True, # 允许为空，方便后续的转让队长或队长退出逻辑
        blank=True
    )

    # 通过 GroupMembership 中间模型反向关联所有成员
    members = models.ManyToManyField(
        'studentapp.Student',
        through='GroupMembership',
        related_name='member_of_groups',
        verbose_name='团队成员'
    )

    class Meta:
        db_table = 'team'
        verbose_name = '团队/分组'
        verbose_name_plural = verbose_name
        # 确保在同一个互选活动中，团队名称是唯一的
        unique_together = ('event', 'group_name')

    def clean(self):
        """
        模型的自定义验证逻辑。
        在保存或创建时，Django admin 和 ModelForm 会自动调用此方法。
        注意：DRF Serializer 不会自动调用此方法，相关逻辑应在Serializer中实现。
        """
        super().clean()
        if self.captain and self.pk and not self.members.filter(pk=self.captain.pk).exists():
            raise ValidationError(f"队长 {self.captain.stu_name} 必须是团队的成员。")

        if self.event:
            if self.advisor and not self.event.teachers.filter(pk=self.advisor.pk).exists():
                raise ValidationError(f"指导老师 {self.advisor.teacher_name} 未参与此互选活动。")

            # 检查所有成员是否都参与了该活动
            # 这个检查更适合在添加成员时进行，而不是在保存团队时
            # for member in self.members.all():
            #     if not self.event.students.filter(pk=member.pk).exists():
            #         raise ValidationError(f"成员 {member.stu_name} 未参与此互选活动。")

    def __str__(self):
        return self.group_name


class GroupMembership(models.Model):
    """
    团队成员关系模型 (中间表)
    这个模型是核心，它保证了一个学生只能加入一个团队。
    """
    student = models.OneToOneField(
        'studentapp.Student',
        on_delete=models.CASCADE,
        primary_key=True,
        related_name='membership'
    )
    group = models.ForeignKey(
        Group,
        on_delete=models.CASCADE,
        related_name='memberships'
    )
    date_joined = models.DateTimeField(auto_now_add=True, verbose_name='加入时间')

    class Meta:
        db_table = 'team_membership'
        verbose_name = '团队成员关系'
        verbose_name_plural = verbose_name

    def __str__(self):
        return f"{self.student.stu_name} -> {self.group.group_name}"