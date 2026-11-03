from django.contrib import admin
from django.utils.html import format_html
from django.utils.safestring import mark_safe
from django.urls import reverse
from django.utils import timezone
from .models import Task


class DueStatusFilter(admin.SimpleListFilter):
    """Filter tasks by due status: Overdue, Due Today, Upcoming, or No Due Date."""
    title = 'due status'
    parameter_name = 'due_status'

    def lookups(self, request, model_admin):
        return (
            ('overdue', 'Overdue'),
            ('due_today', 'Due Today'),
            ('upcoming', 'Upcoming'),
            ('no_due_date', 'No Due Date'),
        )

    def queryset(self, request, queryset):
        today = timezone.now().date()
        if self.value() == 'overdue':
            return queryset.filter(completed=False, due_date__lt=today)
        elif self.value() == 'due_today':
            return queryset.filter(completed=False, due_date=today)
        elif self.value() == 'upcoming':
            return queryset.filter(completed=False, due_date__gt=today)
        elif self.value() == 'no_due_date':
            return queryset.filter(due_date__isnull=True)
        return queryset


@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    """
    User Task Management:
    - View all tasks created across the entire application.
    - Clear user ownership identification with links to user profiles.
    - Full details: title, description, priority, completion status, due date.
    - Comprehensive filtering by user, priority, completion status, due status, and date.
    - Quick actions to mark tasks as completed or pending.
    """
    list_display = (
        'title',
        'user_owner',
        'priority_badge',
        'completed',
        'due_date',
        'due_status_badge',
        'created_at'
    )
    list_filter = (
        'completed',
        'priority',
        DueStatusFilter,
        'due_date',
        'created_at',
        'user'
    )
    search_fields = (
        'title',
        'description',
        'user__username',
        'user__email',
        'user__first_name',
        'user__last_name'
    )
    list_editable = ('completed',)
    ordering = ('-created_at',)
    autocomplete_fields = ['user']
    actions = ['mark_as_completed', 'mark_as_pending']

    fieldsets = (
        ('Task Details', {
            'fields': ('title', 'user', 'description')
        }),
        ('Status & Scheduling', {
            'fields': ('priority', 'completed', 'due_date')
        }),
        ('Notification Delivery Tracking', {
            'classes': ('collapse',),
            'fields': (
                'upcoming_reminder_sent',
                'upcoming_reminder_sent_at',
                'overdue_alert_sent',
                'overdue_alert_sent_at'
            )
        }),
        ('Timestamps', {
            'classes': ('collapse',),
            'fields': ('created_at', 'updated_at')
        }),
    )
    readonly_fields = ('created_at', 'updated_at')

    @admin.display(description='Owner', ordering='user__username')
    def user_owner(self, obj):
        user_url = reverse('admin:auth_user_change', args=[obj.user.pk])
        email_str = f" <{obj.user.email}>" if obj.user.email else ""
        return format_html(
            '<a href="{}" title="View user profile" style="font-weight:600;color:#065f46;text-decoration:none;">'
            '{}'
            '</a>'
            '<span style="color:#6b7280;font-size:11px;">{}</span>',
            user_url,
            obj.user.username,
            email_str
        )

    @admin.display(description='Priority', ordering='priority')
    def priority_badge(self, obj):
        colors = {
            'high': ('#fee2e2', '#991b1b', '#ef4444'),
            'medium': ('#fef3c7', '#92400e', '#f59e0b'),
            'low': ('#e0f2fe', '#075985', '#0ea5e9'),
        }
        bg, fg, dot = colors.get(obj.priority, ('#f3f4f6', '#374151', '#9ca3af'))
        return format_html(
            '<span style="display:inline-flex;align-items:center;gap:5px;padding:2px 8px;border-radius:12px;font-size:11px;font-weight:600;background:{};color:{};">'
            '<span style="width:6px;height:6px;border-radius:50%;background:{};"></span>{}</span>',
            bg, fg, dot, obj.get_priority_display()
        )

    @admin.display(description='Status', ordering='completed')
    def status_badge(self, obj):
        if obj.completed:
            return mark_safe(
                '<span style="display:inline-block;padding:2px 8px;border-radius:12px;font-size:11px;font-weight:600;background:#d1fae5;color:#065f46;">'
                '✓ Completed</span>'
            )
        return mark_safe(
            '<span style="display:inline-block;padding:2px 8px;border-radius:12px;font-size:11px;font-weight:600;background:#fef3c7;color:#92400e;">'
            'Pending</span>'
        )

    @admin.display(description='Due Status')
    def due_status_badge(self, obj):
        if not obj.due_date:
            return mark_safe('<span style="color:#9ca3af;font-size:11px;">No due date</span>')
        if obj.completed:
            return mark_safe('<span style="color:#059669;font-size:11px;">Finished</span>')

        today = timezone.now().date()
        if obj.due_date < today:
            days = (today - obj.due_date).days
            return format_html(
                '<span style="display:inline-block;padding:2px 8px;border-radius:12px;font-size:11px;font-weight:600;background:#fee2e2;color:#991b1b;">'
                'Overdue ({}d)</span>',
                days
            )
        elif obj.due_date == today:
            return mark_safe(
                '<span style="display:inline-block;padding:2px 8px;border-radius:12px;font-size:11px;font-weight:600;background:#fef3c7;color:#92400e;">'
                'Due Today</span>'
            )
        else:
            days = (obj.due_date - today).days
            return format_html(
                '<span style="display:inline-block;padding:2px 8px;border-radius:12px;font-size:11px;font-weight:600;background:#ecfdf5;color:#065f46;">'
                'In {} day{}</span>',
                days,
                's' if days != 1 else ''
            )

    @admin.action(description='Mark selected tasks as Completed')
    def mark_as_completed(self, request, queryset):
        count = queryset.update(completed=True)
        self.message_user(request, f"{count} task(s) marked as completed.")

    @admin.action(description='Mark selected tasks as Pending')
    def mark_as_pending(self, request, queryset):
        count = queryset.update(completed=False)
        self.message_user(request, f"{count} task(s) marked as pending.")
