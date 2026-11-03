"""
TaskFlow Background Email Notification Scheduler.
Runs periodically in a lightweight background daemon thread without requiring
external infrastructure like Celery or Redis.
"""

import os
import sys
import time
import threading
import logging
from django.conf import settings

logger = logging.getLogger('tasks')

_scheduler_thread = None
_scheduler_lock = threading.Lock()
_stop_event = threading.Event()


def _scheduler_loop(interval_seconds):
    """Periodic loop running inside background daemon thread."""
    logger.info("Task notification background scheduler loop started (interval: %ds).", interval_seconds)

    # Initial brief pause (e.g., 5 seconds) to let Django complete full startup
    time.sleep(5)

    while not _stop_event.is_set():
        try:
            # Import here to ensure models and apps are fully loaded
            from tasks.email_service import process_and_send_due_notifications
            process_and_send_due_notifications()
        except Exception as exc:
            logger.error("Error in background task notification loop: %s", exc, exc_info=True)

        # Wait for the next check interval or until stopped
        _stop_event.wait(timeout=interval_seconds)

    logger.info("Task notification background scheduler loop stopped.")


def start_notification_scheduler():
    """
    Start the background notification thread if enabled in settings.
    Guards against duplicate thread creation and ensures execution only
    in active web server processes.
    """
    global _scheduler_thread

    # Check if disabled
    if not getattr(settings, 'ENABLE_NOTIFICATION_SCHEDULER', True):
        logger.info("Task notification scheduler is disabled in settings.")
        return

    # Skip during management commands other than runserver
    is_manage = any('manage.py' in arg for arg in sys.argv)
    if is_manage and 'runserver' not in sys.argv:
        return

    command_blacklist = {'test', 'makemigrations', 'migrate', 'collectstatic', 'shell', 'seed_demo_data', 'send_task_reminders'}
    if any(cmd in sys.argv for cmd in command_blacklist):
        return

    # In development with runserver, only start in the reloaded child worker (RUN_MAIN == 'true')
    if 'runserver' in sys.argv and os.environ.get('RUN_MAIN') != 'true':
        return

    with _scheduler_lock:
        if _scheduler_thread is not None and _scheduler_thread.is_alive():
            return

        interval = getattr(settings, 'NOTIFICATION_CHECK_INTERVAL_SECONDS', 3600)
        _stop_event.clear()
        _scheduler_thread = threading.Thread(
            target=_scheduler_loop,
            args=(interval,),
            name='TaskFlowNotificationScheduler',
            daemon=True
        )
        _scheduler_thread.start()
        logger.info("TaskFlow background email notification scheduler thread initiated successfully.")


def stop_notification_scheduler():
    """Signal background thread to terminate."""
    _stop_event.set()
