from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth import get_user_model
from .models import StudentProfile, TeacherProfile

User = get_user_model()


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    fieldsets = BaseUserAdmin.fieldsets + (
        ('额外信息', {
            'fields': ('role', 'real_name', 'student_id', 'phone_number', 
                      'department', 'major', 'grade')
        }),
        ('时间信息', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ('created_at', 'updated_at')
    
    list_display = ('username', 'real_name', 'email', 'role', 
                   'department', 'is_active', 'created_at')
    list_filter = ('role', 'department', 'is_active', 'created_at')
    search_fields = ('username', 'real_name', 'email', 'student_id', 'department')
    ordering = ('-created_at',)


@admin.register(StudentProfile)
class StudentProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'gpa', 'get_department', 'get_major')
    list_filter = ('user__department', 'user__major', 'user__grade')
    search_fields = ('user__username', 'user__real_name', 'research_interests', 'skills')
    raw_id_fields = ('user',)
    
    fieldsets = (
        ('基本信息', {
            'fields': ('user',)
        }),
        ('学术信息', {
            'fields': ('gpa', 'research_interests', 'skills')
        }),
        ('个人介绍', {
            'fields': ('introduction',)
        }),
    )
    
    def get_department(self, obj):
        return obj.user.department
    get_department.short_description = '院系'
    
    def get_major(self, obj):
        return obj.user.major
    get_major.short_description = '专业'


@admin.register(TeacherProfile)
class TeacherProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'title', 'get_department', 'max_students', 
                   'current_students', 'is_accepting')
    list_filter = ('title', 'user__department', 'is_accepting')
    search_fields = ('user__username', 'user__real_name', 'research_areas', 'title')
    raw_id_fields = ('user',)
    
    fieldsets = (
        ('基本信息', {
            'fields': ('user', 'title')
        }),
        ('研究信息', {
            'fields': ('research_areas', 'introduction', 'requirements')
        }),
        ('指导设置', {
            'fields': ('max_students', 'current_students', 'is_accepting')
        }),
    )
    
    def get_department(self, obj):
        return obj.user.department
    get_department.short_description = '院系'
