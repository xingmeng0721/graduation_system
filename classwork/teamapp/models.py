from django.db import models
from django.core.exceptions import ValidationError


class Group(models.Model):
    """
    分组/团队模型
    """
    group_id = models.AutoField(primary_key=True)
    group_name = models.CharField(max_length=255, verbose_name='分组名称')
    project_title = models.CharField(max_length=255, verbose_name="项目标题", blank=True)
    project_description = models.TextField(verbose_name="项目简介", blank=True)

    event = models.ForeignKey(
        'adminapp.MutualSelectionEvent',
        on_delete=models.CASCADE,
        related_name='groups',
        verbose_name='所属互选活动',
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

    advisor = models.ForeignKey(
        'teacherapp.teacher',
        on_delete=models.SET_NULL,
        related_name='advised_groups',
        verbose_name='最终指导老师',
        null=True,
        blank=True
    )

    captain = models.ForeignKey(
        'studentapp.Student',
        on_delete=models.SET_NULL,
        related_name='led_groups',
        verbose_name='队长',
        null=True,
        blank=True
    )

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
        unique_together = ('event', 'group_name')

    def clean(self):
        """
        模型的自定义验证逻辑。
        """
        super().clean()
        if self.captain and self.pk and not self.members.filter(pk=self.captain.pk).exists():
            raise ValidationError(f"队长 {self.captain.stu_name} 必须是团队的成员。")

        if self.event:
            if self.advisor and not self.event.teachers.filter(pk=self.advisor.pk).exists():
                raise ValidationError(f"指导老师 {self.advisor.teacher_name} 未参与此互选活动。")

        if self.members.count() > self.MEMBERS_LIMIT:
            raise ValidationError(f"团队成员人数不能超过 {self.MEMBERS_LIMIT} 人（含队长）。")

    def __str__(self):
        return self.group_name


class GroupMembership(models.Model):
    """
    团队成员关系模型 (中间表)
    """
    id = models.AutoField(primary_key=True)

    student = models.ForeignKey(
        'studentapp.Student',
        on_delete=models.CASCADE,
        related_name='memberships'
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
        unique_together = [
            ('student', 'group'),
        ]
        indexes = [
            models.Index(fields=['student', 'group']),
        ]

    def clean(self):
        """验证学生是否已在同一活动的其他团队中"""
        if self.group and self.group.event:
            existing = GroupMembership.objects.filter(
                student=self.student,
                group__event=self.group.event
            ).exclude(pk=self.pk)

            if existing.exists():
                existing_group = existing.first().group
                raise ValidationError(
                    f"学生 {self.student.stu_name} 已在活动 '{self.group.event.event_name}' "
                    f"的团队 '{existing_group.group_name}' 中，无法加入多个团队。"
                )

    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.student.stu_name} -> {self.group.group_name} ({self.group.event.event_name})"

class TeacherGroupPreference(models.Model):
    """
    存储教师对团队的志愿选择。
    """
    teacher = models.ForeignKey('teacherapp.teacher', on_delete=models.CASCADE, related_name='group_preferences')
    group = models.ForeignKey(Group, on_delete=models.CASCADE, related_name='teacher_preferences')
    preference_rank = models.PositiveIntegerField(verbose_name='志愿顺序')

    class Meta:
        db_table = 'teacher_group_preference'
        verbose_name = '教师组队志愿'
        verbose_name_plural = verbose_name
        unique_together = [
            ('teacher', 'group'),
        ]
        indexes = [
            models.Index(fields=['teacher', 'preference_rank']),
        ]

    def clean(self):
        """
        自定义验证：确保教师在同一活动中，每个志愿排名只能用一次
        """
        if self.group and self.group.event:
            existing = TeacherGroupPreference.objects.filter(
                teacher=self.teacher,
                group__event=self.group.event,
                preference_rank=self.preference_rank
            ).exclude(pk=self.pk)

            if existing.exists():
                raise ValidationError(
                    f"您已在活动 '{self.group.event.event_name}' 中将第 {self.preference_rank} "
                    f"志愿用于小组 '{existing.first().group.group_name}'，不能重复使用。"
                )

    def __str__(self):
        return f"{self.teacher.teacher_name} - {self.preference_rank}志愿: {self.group.group_name}"


class ProvisionalAssignment(models.Model):
    """
    存储自动分配或手动调整后的临时（草稿）分配结果。
    """
    event = models.ForeignKey(
        'adminapp.MutualSelectionEvent',
        on_delete=models.CASCADE,
        related_name='provisional_assignments'
    )
    group = models.OneToOneField(
        Group,
        on_delete=models.CASCADE,
        related_name='provisional_assignment'
    )
    teacher = models.ForeignKey(
        'teacherapp.teacher',
        on_delete=models.CASCADE,
        related_name='provisional_assignments'
    )
    ASSIGNMENT_TYPE_CHOICES = [
        ('auto', '自动分配'),
        ('manual', '手动调整'),
    ]
    assignment_type = models.CharField(
        max_length=10,
        choices=ASSIGNMENT_TYPE_CHOICES,
        default='auto'
    )
    score = models.FloatField(default=0, help_text="匹配得分")
    explanation = models.CharField(max_length=255, blank=True, help_text="匹配原因说明")

    class Meta:
        db_table = 'provisional_assignment'
        verbose_name = '临时分配结果'
        verbose_name_plural = verbose_name
        unique_together = ('event', 'group')

    def __str__(self):
        return f"{self.event.event_name}: {self.group.group_name} -> {self.teacher.teacher_name}"