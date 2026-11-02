from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta
from accounts.models import Profile
from tasks.models import Task


class Command(BaseCommand):
    help = 'Seeds demo user and tasks matching the reference image'

    def handle(self, *args, **kwargs):
        user, created = User.objects.get_or_create(
            username='akhilesh',
            defaults={
                'email': 'akhilesh@example.com',
                'first_name': 'Akhilesh',
                'last_name': 'Developer',
                'is_staff': True,
                'is_superuser': True,
            }
        )
        user.set_password('Password123!')
        user.save()
        Profile.objects.get_or_create(user=user)

        # Remove previous tasks to avoid duplicates
        Task.objects.filter(user=user).delete()

        today = timezone.now().date()

        # Tasks exactly matching the reference screenshot:
        tasks_data = [
            # The 5 visible in the screenshot table:
            ("Design login and signup pages", "Build responsive split auth views matching Figma", "high", False, today),
            ("Implement task CRUD with modal", "Create modals for Add, Edit and Delete with validation", "medium", True, today - timedelta(days=3)),
            ("Add report and dashboard charts", "Integrate Chart.js for donut, bar and line analytics", "low", False, today + timedelta(days=3)),
            ("Integrate AI task suggestion", "Call Groq API to auto-suggest task descriptions", "high", False, today + timedelta(days=4)),
            ("Test and fix validation errors", "Comprehensive validation on client and server sides", "medium", True, today - timedelta(days=5)),

            # 4 Overdue tasks:
            ("Setup initial Django project", "Config, ASGI, WSGI and SQLite connection", "medium", False, today - timedelta(days=7)),
            ("Draft database schema", "Entities for User, Profile and Task", "high", False, today - timedelta(days=4)),
            ("Configure environment variables", "Load .env secrets securely", "low", False, today - timedelta(days=2)),
            ("Setup static files and CSS variables", "Create color palette tokens and layout grid", "high", False, today - timedelta(days=1)),

            # Additional Completed tasks (total 12 completed):
            ("Setup base HTML templates", "Modular base.html with sidebar and topbar", "medium", True, today - timedelta(days=6)),
            ("Install dependencies", "Django, python-dotenv, requests", "low", True, today - timedelta(days=6)),
            ("Configure password validators", "Enforce length and complexity requirements", "high", True, today - timedelta(days=5)),
            ("Build user profile settings", "Edit name, email and password update forms", "medium", True, today - timedelta(days=4)),
            ("Create custom SVG logo", "Design gradient brand icon", "low", True, today - timedelta(days=4)),
            ("Implement AJAX status toggle", "One-click complete checkbox without page reload", "high", True, today - timedelta(days=3)),
            ("Setup Chart.js CDN", "Load modern charts in dashboard and reports", "low", True, today - timedelta(days=2)),
            ("Create floating AI chatbot widget", "Expandable chat panel with typing animation", "high", True, today - timedelta(days=2)),
            ("Add search and filter bar", "Live status pills and priority dropdown", "medium", True, today - timedelta(days=1)),
            ("Write 25 automated unit tests", "Test auth, CRUD, permissions and Groq mocks", "high", True, today - timedelta(days=1)),

            # Additional Pending tasks (total 8 pending, including 3 above + 5 here):
            ("Perform cross-browser check", "Test in Chrome, Firefox and Edge", "medium", False, today + timedelta(days=2)),
            ("Optimize mobile viewport padding", "Ensure tables adapt smoothly to cards", "low", False, today + timedelta(days=5)),
            ("Review accessibility contrast", "Check WCAG AA compliance on indigo buttons", "low", False, today + timedelta(days=6)),
            ("Refactor CSS variables", "Clean up unused helper classes", "medium", False, today + timedelta(days=7)),
            ("Write user documentation", "Comprehensive README with setup instructions", "medium", False, today + timedelta(days=8)),
        ]

        for title, desc, priority, completed, due in tasks_data:
            Task.objects.create(
                user=user,
                title=title,
                description=desc,
                priority=priority,
                completed=completed,
                due_date=due
            )

        self.stdout.write(self.style.SUCCESS(
            f"Successfully seeded demo user 'akhilesh' (password: 'Password123!') with {len(tasks_data)} tasks!"
        ))

