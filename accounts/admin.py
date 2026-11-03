from django.contrib import admin
from django.contrib.auth.models import User
from django.contrib.auth.admin import UserAdmin
from django.utils.html import format_html
from django.urls import reverse
from django.utils import timezone
from .models import Profile
from tasks.models import Task


# =====================================================================
# Inlines for User Admin
# =====================================================================

class ProfileInline(admin.StackedInline):
    """Inline profile manager embedded directly inside User change view."""
    model = Profile
    can_delete = False
    extra = 0
    verbose_name = 'User Profile'
    verbose_name_plural = 'User Profile'
    fields = ('avatar', 'bio', 'created_at', 'updated_at')
    readonly_fields = ('created_at', 'updated_at')


class TaskInline(admin.TabularInline):
    """Inline task manager allowing admins to inspect and navigate user tasks."""
    model = Task
    extra = 0
    verbose_name = 'Task Owned by User'
    verbose_name_plural = 'Tasks Owned by User'
    fields = ('title', 'priority', 'completed', 'due_date', 'created_at')
    readonly_fields = ('created_at',)
    show_change_link = True
    ordering = ('-created_at',)


# =====================================================================
# Custom User Admin
# =====================================================================

class CustomUserAdmin(UserAdmin):
    """
    Enhanced User Administration:
    - View, search, and multi-criteria filter users.
    - Inline Profile and Tasks.
    - Quick activation/deactivation via list_editable and bulk actions.
    - Live task statistics for every registered user.
    """
    inlines = (ProfileInline, TaskInline)
    list_display = (
        'username',
        'email',
        'get_full_name',
        'is_active',
        'is_staff',
        'is_superuser',
        'task_stats_display',
        'date_joined',
        'last_login'
    )
    list_filter = ('is_active', 'is_staff', 'is_superuser', 'date_joined', 'last_login')
    search_fields = ('username', 'first_name', 'last_name', 'email')
    ordering = ('-date_joined',)
    list_editable = ('is_active',)
    actions = ['activate_users', 'deactivate_users']

    @admin.display(description='Task Statistics (Total / Pending / Overdue)')
    def task_stats_display(self, obj):
        total = obj.tasks.count()
        if total == 0:
            return format_html('<span style="color:#9ca3af;font-size:12px;">0 tasks</span>')

        pending = obj.tasks.filter(completed=False).count()
        today = timezone.now().date()
        overdue = obj.tasks.filter(completed=False, due_date__lt=today).count()

        task_list_url = reverse('admin:tasks_task_changelist') + f'?user__id__exact={obj.id}'

        pending_style = (
            'background:#fef3c7;color:#92400e;padding:2px 7px;border-radius:10px;font-size:11px;font-weight:600;'
            if pending > 0 else
            'background:#f3f4f6;color:#6b7280;padding:2px 7px;border-radius:10px;font-size:11px;'
        )
        overdue_style = (
            'background:#fee2e2;color:#991b1b;padding:2px 7px;border-radius:10px;font-size:11px;font-weight:600;'
            if overdue > 0 else
            'background:#f3f4f6;color:#6b7280;padding:2px 7px;border-radius:10px;font-size:11px;'
        )

        return format_html(
            '<a href="{}" title="Click to view all tasks owned by {}" style="text-decoration:none;display:inline-flex;align-items:center;gap:6px;">'
            '<strong style="color:#065f46;font-size:12px;">{} total</strong>'
            '<span style="{}">{} pending</span>'
            '<span style="{}">{} overdue</span>'
            '</a>',
            task_list_url,
            obj.username,
            total,
            pending_style,
            pending,
            overdue_style,
            overdue
        )

    @admin.action(description='Activate selected user accounts')
    def activate_users(self, request, queryset):
        count = queryset.update(is_active=True)
        self.message_user(request, f"{count} user account(s) successfully activated.")

    @admin.action(description='Deactivate selected user accounts')
    def deactivate_users(self, request, queryset):
        target = queryset.exclude(pk=request.user.pk)
        count = target.update(is_active=False)
        self.message_user(request, f"{count} user account(s) successfully deactivated.")


# =====================================================================
# Profile Admin
# =====================================================================

@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'get_email', 'has_avatar', 'created_at', 'updated_at')
    search_fields = ('user__username', 'user__email', 'bio')
    list_filter = ('created_at',)
    readonly_fields = ('created_at', 'updated_at')

    @admin.display(description='Email', ordering='user__email')
    def get_email(self, obj):
        return obj.user.email


# =====================================================================
# Register User with CustomUserAdmin
# =====================================================================

admin.site.unregister(User)
admin.site.register(User, CustomUserAdmin)


# =====================================================================
# Admin Site Branding, Security & Dashboard Statistics
# =====================================================================

admin.site.site_header = "TaskFlow Administration"
admin.site.site_title = "TaskFlow Admin Portal"
admin.site.index_title = "TaskFlow Management & Analytics Dashboard"


def superuser_only_has_permission(request):
    """
    Security Gate:
    Enforce that ONLY active Django superusers can access the admin management system.
    Normal users and non-superuser staff are strictly blocked.
    """
    return bool(request.user and request.user.is_active and request.user.is_superuser)


admin.site.has_permission = superuser_only_has_permission


original_admin_index = admin.site.index


def admin_dashboard_index(request, extra_context=None):
    """
    Inject live platform analytics into the admin index dashboard:
    - Total users, active users, inactive users.
    - Total tasks, pending tasks, completed tasks, overdue tasks, due today tasks.
    """
    today = timezone.now().date()
    total_users = User.objects.count()
    active_users = User.objects.filter(is_active=True).count()
    inactive_users = total_users - active_users

    total_tasks = Task.objects.count()
    completed_tasks = Task.objects.filter(completed=True).count()
    pending_tasks = total_tasks - completed_tasks
    overdue_tasks = Task.objects.filter(completed=False, due_date__lt=today).count()
    due_today_tasks = Task.objects.filter(completed=False, due_date=today).count()

    stats = {
        'total_users': total_users,
        'active_users': active_users,
        'inactive_users': inactive_users,
        'total_tasks': total_tasks,
        'pending_tasks': pending_tasks,
        'completed_tasks': completed_tasks,
        'overdue_tasks': overdue_tasks,
        'due_today_tasks': due_today_tasks,
    }

    extra_context = extra_context or {}
    extra_context['dashboard_stats'] = stats
    return original_admin_index(request, extra_context=extra_context)


admin.site.index = admin_dashboard_index
