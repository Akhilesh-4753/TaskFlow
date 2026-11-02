from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.db.models import Count
from django.db.models.functions import TruncDate
from tasks.models import Task
import json


@login_required
def report_dashboard_view(request):
    """Reports page with database-backed charts and statistics."""
    user = request.user
    tasks = Task.objects.filter(user=user)

    total = tasks.count()
    completed = tasks.filter(completed=True).count()
    pending = tasks.filter(completed=False).count()
    completion_rate = round((completed / total * 100), 1) if total > 0 else 0

    # Tasks by priority
    priority_data = {
        'high': tasks.filter(priority='high').count(),
        'medium': tasks.filter(priority='medium').count(),
        'low': tasks.filter(priority='low').count(),
    }

    # Tasks created over last 7 days
    from django.utils import timezone
    from datetime import timedelta
    today = timezone.now().date()
    week_labels = []
    week_counts = []
    for i in range(6, -1, -1):
        day = today - timedelta(days=i)
        count = tasks.filter(created_at__date=day).count()
        week_labels.append(day.strftime('%a'))
        week_counts.append(count)

    # Recent completed tasks
    recently_completed = tasks.filter(completed=True).order_by('-updated_at')[:5]
    # Pending tasks
    pending_tasks = tasks.filter(completed=False).order_by('due_date', '-created_at')[:5]
    # High priority pending tasks
    high_priority_tasks = tasks.filter(priority='high', completed=False).order_by('-created_at')[:5]

    # Overdue tasks
    overdue_count = sum(1 for t in tasks.filter(completed=False) if t.is_overdue())
    pending_only = max(0, pending - overdue_count)

    context = {
        'active_page': 'reports',
        'total': total,
        'completed': completed,
        'pending': pending,
        'completion_rate': completion_rate,
        'overdue_count': overdue_count,
        'priority_data_json': json.dumps(priority_data),
        'week_labels_json': json.dumps(week_labels),
        'week_counts_json': json.dumps(week_counts),
        'status_data_json': json.dumps({'completed': completed, 'pending': pending_only, 'overdue': overdue_count}),
        'recently_completed': recently_completed,
        'pending_tasks': pending_tasks,
        'high_priority_tasks': high_priority_tasks,
    }
    return render(request, 'reports/report_dashboard.html', context)

