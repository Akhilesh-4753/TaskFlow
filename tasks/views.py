from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import ensure_csrf_cookie
from django.contrib import messages
from django.http import JsonResponse
from django.db.models import Q
from django.core.paginator import Paginator
from django.utils import timezone
from .models import Task
from .forms import TaskForm


def get_user_task_stats(user):
    """Return task statistics for a given user."""
    tasks = Task.objects.filter(user=user)
    total = tasks.count()
    completed = tasks.filter(completed=True).count()
    pending = tasks.filter(completed=False).count()
    high_priority = tasks.filter(priority='high', completed=False).count()
    overdue = sum(1 for t in tasks.filter(completed=False) if t.is_overdue())
    return {
        'total': total,
        'completed': completed,
        'pending': pending,
        'high_priority': high_priority,
        'overdue': overdue,
    }


@login_required
@ensure_csrf_cookie
def dashboard_view(request):
    """Main dashboard with summary stats and recent tasks."""
    stats = get_user_task_stats(request.user)
    recent_tasks = Task.objects.filter(user=request.user).order_by('-created_at')[:5]

    # Calculate weekly activity for the This Week chart
    from datetime import timedelta
    today = timezone.now().date()
    week_labels = []
    week_counts = []
    for i in range(6, -1, -1):
        day = today - timedelta(days=i)
        count = Task.objects.filter(user=request.user, created_at__date=day).count()
        week_labels.append(day.strftime('%a'))
        week_counts.append(count)

    # Handle create task from dashboard
    if request.method == 'POST':
        form = TaskForm(request.POST)
        if form.is_valid():
            task = form.save(commit=False)
            task.user = request.user
            task.save()
            messages.success(request, f'Task "{task.title}" created successfully!')
            return redirect('tasks:dashboard')
        else:
            messages.error(request, 'Please correct the form errors.')
    else:
        form = TaskForm()

    import json
    context = {
        'stats': stats,
        'recent_tasks': recent_tasks,
        'form': form,
        'active_page': 'dashboard',
        'week_labels_json': json.dumps(week_labels),
        'week_counts_json': json.dumps(week_counts),
    }
    return render(request, 'tasks/dashboard.html', context)


@login_required
@ensure_csrf_cookie
def task_list_view(request):
    """All tasks page with search, filter, and pagination."""
    tasks = Task.objects.filter(user=request.user)

    # Search
    search_query = request.GET.get('search', '').strip()
    if search_query:
        tasks = tasks.filter(
            Q(title__icontains=search_query) | Q(description__icontains=search_query)
        )

    # Filter by status / overdue
    status_filter = request.GET.get('status', 'all')
    is_overdue = request.GET.get('overdue') == '1'
    if is_overdue:
        tasks = tasks.filter(completed=False, due_date__lt=timezone.now().date())
    elif status_filter == 'completed':
        tasks = tasks.filter(completed=True)
    elif status_filter == 'pending':
        tasks = tasks.filter(completed=False)

    # Filter by priority
    priority_filter = request.GET.get('priority', 'all')
    if priority_filter in ['low', 'medium', 'high']:
        tasks = tasks.filter(priority=priority_filter)

    # Sorting
    sort_by = request.GET.get('sort', '-created_at')
    allowed_sorts = ['created_at', '-created_at', 'due_date', '-due_date', 'title', '-title', 'priority']
    if sort_by in allowed_sorts:
        tasks = tasks.order_by(sort_by)

    # Pagination
    paginator = Paginator(tasks, 10)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)

    stats = get_user_task_stats(request.user)

    # Handle create task from task list
    if request.method == 'POST':
        form = TaskForm(request.POST)
        if form.is_valid():
            task = form.save(commit=False)
            task.user = request.user
            task.save()
            messages.success(request, f'Task "{task.title}" created successfully!')
            return redirect('tasks:task_list')
        else:
            messages.error(request, 'Please correct the form errors.')
    else:
        form = TaskForm()

    context = {
        'page_obj': page_obj,
        'tasks': page_obj,
        'form': form,
        'stats': stats,
        'search_query': search_query,
        'status_filter': status_filter,
        'is_overdue': is_overdue,
        'priority_filter': priority_filter,
        'sort_by': sort_by,
        'active_page': 'tasks',
        'total_count': tasks.count(),
        'all_count': Task.objects.filter(user=request.user).count(),
        'pending_count': Task.objects.filter(user=request.user, completed=False).count(),
        'completed_count': Task.objects.filter(user=request.user, completed=True).count(),
        'overdue_count': sum(1 for t in Task.objects.filter(user=request.user, completed=False) if t.is_overdue()),
    }
    return render(request, 'tasks/task_list.html', context)


@login_required
def task_create_view(request):
    """AJAX-friendly task creation endpoint."""
    if request.method == 'POST':
        form = TaskForm(request.POST)
        if form.is_valid():
            task = form.save(commit=False)
            task.user = request.user
            task.save()
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': True,
                    'message': f'Task "{task.title}" created successfully!',
                    'task_id': task.id,
                })
            messages.success(request, f'Task "{task.title}" created successfully!')
            return redirect(request.POST.get('next', 'tasks:task_list'))
        else:
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                errors = {field: [str(e) for e in errs] for field, errs in form.errors.items()}
                return JsonResponse({'success': False, 'errors': errors}, status=400)
            messages.error(request, 'Please correct the form errors.')
            return redirect(request.POST.get('next', 'tasks:task_list'))
    return redirect('tasks:task_list')


@login_required
def task_edit_view(request, pk):
    """Edit an existing task (AJAX-friendly)."""
    task = get_object_or_404(Task, pk=pk, user=request.user)

    if request.method == 'POST':
        form = TaskForm(request.POST, instance=task)
        if form.is_valid():
            form.save()
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': True,
                    'message': f'Task "{task.title}" updated successfully!',
                })
            messages.success(request, f'Task "{task.title}" updated successfully!')
            return redirect(request.POST.get('next', 'tasks:task_list'))
        else:
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                errors = {field: [str(e) for e in errs] for field, errs in form.errors.items()}
                return JsonResponse({'success': False, 'errors': errors}, status=400)
            messages.error(request, 'Please correct the form errors.')

    # GET: return task data as JSON for modal pre-population
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        data = {
            'id': task.id,
            'title': task.title,
            'description': task.description,
            'priority': task.priority,
            'due_date': task.due_date.strftime('%Y-%m-%d') if task.due_date else '',
            'completed': task.completed,
        }
        return JsonResponse({'success': True, 'task': data})

    return redirect('tasks:task_list')


@login_required
def task_delete_view(request, pk):
    """Delete a task (POST only)."""
    task = get_object_or_404(Task, pk=pk, user=request.user)

    if request.method == 'POST':
        title = task.title
        task.delete()
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': True, 'message': f'Task "{title}" deleted.'})
        messages.success(request, f'Task "{title}" deleted.')
        return redirect('tasks:task_list')

    return JsonResponse({'success': False, 'message': 'Invalid request.'}, status=405)


@login_required
def task_toggle_view(request, pk):
    """Toggle or set task completion status (POST)."""
    task = get_object_or_404(Task, pk=pk, user=request.user)

    if request.method == 'POST':
        import json
        desired_completed = None
        if request.body:
            try:
                payload = json.loads(request.body)
                if 'completed' in payload:
                    desired_completed = bool(payload['completed'])
            except Exception:
                pass

        if desired_completed is None and 'completed' in request.POST:
            val = request.POST.get('completed')
            desired_completed = str(val).lower() in ('true', '1')

        if desired_completed is not None:
            task.completed = desired_completed
        else:
            task.completed = not task.completed

        task.save()
        status_text = 'completed' if task.completed else 'pending'
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'success': True,
                'task_id': task.id,
                'completed': task.completed,
                'status_text': status_text,
                'message': f'Task marked as {status_text}.',
            })
        messages.success(request, f'Task marked as {status_text}.')
        return redirect(request.POST.get('next', 'tasks:task_list'))

    return JsonResponse({'success': False, 'message': 'Invalid request.'}, status=405)


@login_required
def task_bulk_toggle_view(request):
    """Bulk update task completion status for user tasks (POST)."""
    if request.method == 'POST':
        import json
        task_ids = []
        completed = True
        if request.body:
            try:
                payload = json.loads(request.body)
                task_ids = payload.get('task_ids', [])
                if 'completed' in payload:
                    completed = bool(payload.get('completed'))
            except Exception:
                pass

        if not task_ids and 'task_ids' in request.POST:
            task_ids = request.POST.getlist('task_ids')
            if 'completed' in request.POST:
                completed = str(request.POST.get('completed')).lower() in ('true', '1')

        if not isinstance(task_ids, list):
            task_ids = [task_ids]

        updated_count = Task.objects.filter(
            user=request.user,
            id__in=task_ids
        ).update(completed=completed)

        status_text = 'completed' if completed else 'pending'
        return JsonResponse({
            'success': True,
            'updated_count': updated_count,
            'completed': completed,
            'status_text': status_text,
            'message': f'{updated_count} tasks marked as {status_text}.',
        })

    return JsonResponse({'success': False, 'message': 'Invalid request.'}, status=405)


