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
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Task'
        verbose_name_plural = 'Tasks'

    def __str__(self):
        return f"{self.title} ({self.user.username})"

    def get_status_display_text(self):
        return 'Completed' if self.completed else 'Pending'

    def is_overdue(self):
        """Check if the task is overdue (pending and past due date)."""
        if self.due_date and not self.completed:
            return self.due_date < timezone.now().date()
        return False

