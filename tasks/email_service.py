"""
TaskFlow Email Notification Service.
Handles automated upcoming due date reminders and overdue task alerts
using Django's EmailMultiAlternatives, HTML templates, and secure SMTP configuration.
"""

import logging
from datetime import timedelta
from collections import defaultdict
from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils import timezone
from .models import Task

logger = logging.getLogger('tasks')

UPCOMING_SUBJECT = 'Task Due Date Reminder – Action Required'
OVERDUE_SUBJECT_PREFIX = 'Overdue Task Alert – '


def get_user_display_name(user):
    """Return friendly name for greeting: Full Name or username."""
    full_name = user.get_full_name()
    return full_name if full_name else user.username


def send_upcoming_reminder_email(user, tasks):
    """
    Send an upcoming task reminder email containing an HTML table of tasks
    approaching their due dates. Marks tasks as upcoming_reminder_sent=True.
    """
    if not user.email:
        logger.warning(
            "Skipping upcoming reminder for user '%s': No registered email address found.",
            user.username
        )
        return False

    if not tasks:
        return False

    user_name = get_user_display_name(user)
    subject = UPCOMING_SUBJECT
    intro_message = (
        "This is a reminder about your pending tasks. Please review the details below "
        "and complete them before or as soon as possible after their due dates."
    )

    context = {
        'user_name': user_name,
        'tasks': tasks,
        'email_subject': subject,
        'intro_message': intro_message,
        'app_url': getattr(settings, 'APP_URL', 'http://127.0.0.1:8000/tasks/list/'),
    }

    try:
        html_content = render_to_string('emails/task_notification.html', context)
        text_content = render_to_string('emails/task_notification.txt', context)

        from_email = getattr(settings, 'DEFAULT_FROM_EMAIL', 'TaskFlow <noreply@taskflow.local>')
        msg = EmailMultiAlternatives(
            subject=subject,
            body=text_content,
            from_email=from_email,
            to=[user.email]
        )
        msg.attach_alternative(html_content, 'text/html')
        msg.send(fail_silently=False)

        now = timezone.now()
        task_ids = []
        for task in tasks:
            task.upcoming_reminder_sent = True
            task.upcoming_reminder_sent_at = now
            task.save(update_fields=['upcoming_reminder_sent', 'upcoming_reminder_sent_at'])
            task_ids.append(task.id)

        logger.info(
            "Sent upcoming reminder email to '%s' for tasks %s.",
            user.email,
            task_ids
        )
        return True

    except Exception as exc:
        logger.error(
            "Failed to send upcoming reminder email to '%s': %s",
            user.email,
            exc,
            exc_info=True
        )
        return False


def send_overdue_alert_email(user, task):
    """
    Send an overdue task alert email for a specific overdue task with an HTML table.
    Subject: 'Overdue Task Alert – [Task Title]'
    Marks task as overdue_alert_sent=True.
    """
    if not user.email:
        logger.warning(
            "Skipping overdue alert for user '%s' on task '%s': No registered email address.",
            user.username,
            task.title
        )
        return False

    user_name = get_user_display_name(user)
    subject = f"{OVERDUE_SUBJECT_PREFIX}{task.title}"
    intro_message = (
        f"This is an urgent alert that your task '{task.title}' has passed its scheduled "
        "due date. Please review the details below and complete or reschedule it as soon as possible."
    )

    context = {
        'user_name': user_name,
        'tasks': [task],
        'email_subject': subject,
        'intro_message': intro_message,
        'app_url': getattr(settings, 'APP_URL', 'http://127.0.0.1:8000/tasks/list/'),
    }

    try:
        html_content = render_to_string('emails/task_notification.html', context)
        text_content = render_to_string('emails/task_notification.txt', context)

        from_email = getattr(settings, 'DEFAULT_FROM_EMAIL', 'TaskFlow <noreply@taskflow.local>')
        msg = EmailMultiAlternatives(
            subject=subject,
            body=text_content,
            from_email=from_email,
            to=[user.email]
        )
        msg.attach_alternative(html_content, 'text/html')
        msg.send(fail_silently=False)

        task.overdue_alert_sent = True
        task.overdue_alert_sent_at = timezone.now()
        task.save(update_fields=['overdue_alert_sent', 'overdue_alert_sent_at'])

        logger.info(
            "Sent overdue alert email to '%s' for task '%s' (ID: %s).",
            user.email,
            task.title,
            task.id
        )
        return True

    except Exception as exc:
        logger.error(
            "Failed to send overdue alert email to '%s' for task '%s': %s",
            user.email,
            task.title,
            exc,
            exc_info=True
        )
        return False


def process_and_send_due_notifications():
    """
    Main notification routine:
    1. Identifies overdue pending tasks (due_date < today and overdue_alert_sent=False)
       and sends individual overdue alert emails.
    2. Identifies upcoming pending tasks (today <= due_date <= today + days and upcoming_reminder_sent=False)
       and sends consolidated upcoming reminder emails grouped by user.
    3. Excludes completed tasks and tasks without due dates.
    4. Prevents duplicate notifications using database tracking flags.
    """
    today = timezone.now().date()
    days_threshold = getattr(settings, 'TASK_REMINDER_DAYS_BEFORE_DUE', 1)
    upcoming_limit = today + timedelta(days=days_threshold)

    stats = {
        'overdue_emails_sent': 0,
        'upcoming_emails_sent': 0,
        'overdue_tasks_count': 0,
        'upcoming_tasks_count': 0,
        'errors': 0,
    }

    # 1. Process Overdue Tasks (only pending, due_date < today, not yet alerted)
    overdue_tasks = Task.objects.filter(
        completed=False,
        due_date__isnull=False,
        due_date__lt=today,
        overdue_alert_sent=False
    ).select_related('user').order_by('due_date')

    stats['overdue_tasks_count'] = overdue_tasks.count()

    for task in overdue_tasks:
        success = send_overdue_alert_email(task.user, task)
        if success:
            stats['overdue_emails_sent'] += 1
        else:
            stats['errors'] += 1

    # 2. Process Upcoming Tasks (only pending, today <= due_date <= upcoming_limit, not yet reminded)
    upcoming_tasks = Task.objects.filter(
        completed=False,
        due_date__isnull=False,
        due_date__gte=today,
        due_date__lte=upcoming_limit,
        upcoming_reminder_sent=False
    ).select_related('user').order_by('due_date')

    stats['upcoming_tasks_count'] = upcoming_tasks.count()

    # Group upcoming tasks by user
    upcoming_by_user = defaultdict(list)
    for task in upcoming_tasks:
        upcoming_by_user[task.user].append(task)

    for user, tasks_list in upcoming_by_user.items():
        success = send_upcoming_reminder_email(user, tasks_list)
        if success:
            stats['upcoming_emails_sent'] += 1
        else:
            stats['errors'] += 1

    logger.info(
        "Notification check complete: %d overdue alerts sent, %d upcoming reminder emails sent (%d errors).",
        stats['overdue_emails_sent'],
        stats['upcoming_emails_sent'],
        stats['errors']
    )
    return stats

