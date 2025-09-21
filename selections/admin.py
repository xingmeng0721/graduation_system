from django.contrib import admin
from .models import MentorSelection, TeacherSelection, SelectionPeriod


@admin.register(MentorSelection)
class MentorSelectionAdmin(admin.ModelAdmin):
    list_display = ('get_applicant', 'teacher', 'selection_type', 'status', 
                   'priority', 'applied_at', 'processed_at')
    list_filter = ('selection_type', 'status', 'applied_at', 'processed_at')
    search_fields = ('student__username', 'student__real_name', 'team__name',
                    'teacher__username', 'teacher__real_name')
    raw_id_fields = ('student', 'team', 'teacher')
    date_hierarchy = 'applied_at'
    
    fieldsets = (
        ('申请对象', {
            'fields': ('student', 'team', 'selection_type')
        }),
        ('导师信息', {
            'fields': ('teacher',)
        }),
        ('申请信息', {
            'fields': ('status', 'priority', 'application_message', 'response_message')
        }),
        ('时间信息', {
            'fields': ('applied_at', 'processed_at'),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ('applied_at',)
    
    def get_applicant(self, obj):
        return obj.applicant_name
    get_applicant.short_description = '申请者'


@admin.register(TeacherSelection)
class TeacherSelectionAdmin(admin.ModelAdmin):
    list_display = ('teacher', 'get_target', 'status', 'created_at', 'updated_at')
    list_filter = ('status', 'created_at', 'updated_at')
    search_fields = ('teacher__username', 'teacher__real_name',
                    'student__username', 'student__real_name', 'team__name')
    raw_id_fields = ('teacher', 'student', 'team')
    date_hierarchy = 'created_at'
    
    fieldsets = (
        ('导师信息', {
            'fields': ('teacher',)
        }),
        ('目标对象', {
            'fields': ('student', 'team')
        }),
        ('选择信息', {
            'fields': ('status', 'message')
        }),
        ('时间信息', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ('created_at', 'updated_at')
    
    def get_target(self, obj):
        if obj.team:
            return f"团队: {obj.team.name}"
        return f"学生: {obj.student.real_name or obj.student.username}"
    get_target.short_description = '目标'


@admin.register(SelectionPeriod)
class SelectionPeriodAdmin(admin.ModelAdmin):
    list_display = ('name', 'is_active', 'student_selection_start', 
                   'student_selection_end', 'teacher_selection_start', 
                   'teacher_selection_end')
    list_filter = ('is_active', 'student_selection_start', 'teacher_selection_start')
    search_fields = ('name', 'description')
    date_hierarchy = 'student_selection_start'
    
    fieldsets = (
        ('基本信息', {
            'fields': ('name', 'description', 'is_active')
        }),
        ('学生选择时间', {
            'fields': ('student_selection_start', 'student_selection_end')
        }),
        ('导师选择时间', {
            'fields': ('teacher_selection_start', 'teacher_selection_end')
        }),
        ('时间信息', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ('created_at', 'updated_at')
