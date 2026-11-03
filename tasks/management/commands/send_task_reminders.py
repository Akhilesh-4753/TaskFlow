"""
Django management command to check task due dates and send automated email notifications.
Usage:
    python manage.py send_task_reminders
    python manage.py send_task_reminders --daemon --interval 3600
"""

import time
import logging
from django.core.management.base import BaseCommand
from tasks.email_service import process_and_send_due_notifications

logger = logging.getLogger('tasks')


class Command(BaseCommand):
    help = 'Check pending tasks for upcoming due dates and overdue status, and send automated email reminders.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--daemon',
            action='store_true',
            help='Run continuously in background daemon loop.'
        )
        parser.add_argument(
            '--interval',
            type=int,
            default=3600,
            help='Interval in seconds between notification checks when running in daemon mode (default: 3600).'
        )

    def handle(self, *args, **options):
        is_daemon = options.get('daemon', False)
        interval = options.get('interval', 3600)

        self.stdout.write(self.style.NOTICE("TaskFlow Automated Email Notification Service starting..."))

        if is_daemon:
            self.stdout.write(
                self.style.SUCCESS(f"Running in daemon mode. Checking tasks every {interval} seconds. Press Ctrl+C to stop.")
            )
            try:
                while True:
                    self._run_check()
                    time.sleep(interval)
            except KeyboardInterrupt:
                self.stdout.write(self.style.WARNING("\nTask reminder daemon stopped by user."))
        else:
            self._run_check()

    def _run_check(self):
        self.stdout.write("Checking for pending tasks requiring email notifications...")
        try:
            stats = process_and_send_due_notifications()
            self.stdout.write(self.style.SUCCESS(
                f"Completed: Sent {stats['overdue_emails_sent']}/{stats['overdue_tasks_count']} overdue alert(s), "
                f"{stats['upcoming_emails_sent']} upcoming reminder email(s) for {stats['upcoming_tasks_count']} task(s). "
                f"Errors: {stats['errors']}."
            ))
        except Exception as exc:
            self.stderr.write(self.style.ERROR(f"Error during task reminder check: {exc}"))
            logger.error("Error during task reminder check: %s", exc, exc_info=True)

