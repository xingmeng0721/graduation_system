from django.contrib import admin
from .models import Team, TeamMembership, TeamInvitation


class TeamMembershipInline(admin.TabularInline):
    model = TeamMembership
    extra = 0
    fields = ('student', 'status', 'role', 'applied_at', 'processed_at')
    readonly_fields = ('applied_at',)


@admin.register(Team)
class TeamAdmin(admin.ModelAdmin):
    list_display = ('name', 'leader', 'current_member_count', 'max_members', 
                   'status', 'is_public', 'created_at')
    list_filter = ('status', 'is_public', 'leader__department', 'created_at')
    search_fields = ('name', 'project_title', 'leader__username', 'leader__real_name')
    raw_id_fields = ('leader',)
    inlines = [TeamMembershipInline]
    
    fieldsets = (
        ('基本信息', {
            'fields': ('name', 'leader', 'description', 'max_members', 'is_public')
        }),
        ('项目信息', {
            'fields': ('project_title', 'project_description')
        }),
        ('状态信息', {
            'fields': ('status',)
        }),
        ('时间信息', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ('created_at', 'updated_at')
    
    def current_member_count(self, obj):
        return obj.current_member_count
    current_member_count.short_description = '当前成员数'


@admin.register(TeamMembership)
class TeamMembershipAdmin(admin.ModelAdmin):
    list_display = ('team', 'student', 'status', 'role', 'applied_at', 'processed_at')
    list_filter = ('status', 'applied_at', 'processed_at')
    search_fields = ('team__name', 'student__username', 'student__real_name')
    raw_id_fields = ('team', 'student')
    date_hierarchy = 'applied_at'
    
    fieldsets = (
        ('基本信息', {
            'fields': ('team', 'student', 'status', 'role')
        }),
        ('申请信息', {
            'fields': ('application_message', 'response_message')
        }),
        ('时间信息', {
            'fields': ('applied_at', 'processed_at'),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ('applied_at',)


@admin.register(TeamInvitation)
class TeamInvitationAdmin(admin.ModelAdmin):
    list_display = ('team', 'inviter', 'invitee', 'status', 'created_at', 
                   'responded_at', 'expires_at')
    list_filter = ('status', 'created_at', 'expires_at')
    search_fields = ('team__name', 'inviter__username', 'invitee__username',
                    'inviter__real_name', 'invitee__real_name')
    raw_id_fields = ('team', 'inviter', 'invitee')
    date_hierarchy = 'created_at'
    
    fieldsets = (
        ('基本信息', {
            'fields': ('team', 'inviter', 'invitee', 'status')
        }),
        ('邀请信息', {
            'fields': ('message',)
        }),
        ('时间信息', {
            'fields': ('created_at', 'responded_at', 'expires_at'),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ('created_at',)
