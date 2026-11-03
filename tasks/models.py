from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone


class Task(models.Model):
    """
    Core task model linking each task to its owner.
    Supports priority levels, completion status, and optional due dates.
    """
    PRIORITY_CHOICES = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
    ]

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='tasks',
        help_text='The user who owns this task.'
    )
    title = models.CharField(
        max_length=200,
        help_text='A short, descriptive task title.'
    )
    description = models.TextField(
        blank=True,
        max_length=2000,
        help_text='Optional task description.'
    )
    priority = models.CharField(
        max_length=10,
        choices=PRIORITY_CHOICES,
        default='medium',
        help_text='Task priority level.'
    )
    completed = models.BooleanField(
        default=False,
        help_text='Whether the task is completed.'
    )
    due_date = models.DateField(
        null=True,
        blank=True,
        help_text='Optional due date for the task.'
    )
    # Email notification tracking for duplicate prevention
    upcoming_reminder_sent = models.BooleanField(
        default=False,
        help_text='Whether an upcoming due date reminder email has been sent.'
    )
    overdue_alert_sent = models.BooleanField(
        default=False,
        help_text='Whether an overdue alert email has been sent.'
    )
    upcoming_reminder_sent_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text='Timestamp when the upcoming reminder email was sent.'
    )
    overdue_alert_sent_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text='Timestamp when the overdue alert email was sent.'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Task'
        verbose_name_plural = 'Tasks'

    def __str__(self):
        return f"{self.title} ({self.user.username})"

    def save(self, *args, **kwargs):
        # If task due date is updated to a future date, reset notification flags
        if self.pk:
            original = Task.objects.filter(pk=self.pk).values('due_date').first()
            if original and original['due_date'] != self.due_date and self.due_date:
                today = timezone.now().date()
                if self.due_date >= today:
                    self.overdue_alert_sent = False
                    self.overdue_alert_sent_at = None
                    if self.due_date > today:
                        self.upcoming_reminder_sent = False
                        self.upcoming_reminder_sent_at = None
        super().save(*args, **kwargs)

    def get_status_display_text(self):
        return 'Completed' if self.completed else 'Pending'

    def is_overdue(self):
        """Check if the task is overdue (pending and past due date)."""
        if self.due_date and not self.completed:
            return self.due_date < timezone.now().date()
        return False

    def is_due_today(self):
        """Check if the task is due today."""
        if self.due_date:
            return self.due_date == timezone.now().date()
        return False

