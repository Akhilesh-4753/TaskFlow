from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta
from django.core import mail
from django.core.management import call_command
from tasks.models import Task
from tasks.email_service import (
    process_and_send_due_notifications,
    send_upcoming_reminder_email,
    send_overdue_alert_email,
)


class TaskTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user1 = User.objects.create_user(username='user1', password='Password123!')
        self.user2 = User.objects.create_user(username='user2', password='Password123!')

        self.task1 = Task.objects.create(
            user=self.user1,
            title='User 1 Task',
            description='Description 1',
            priority='high',
            completed=False,
            due_date=timezone.now().date() + timedelta(days=2)
        )

    def test_dashboard_requires_login(self):
        response = self.client.get(reverse('tasks:dashboard'))
        self.assertEqual(response.status_code, 302)

    def test_dashboard_authenticated(self):
        self.client.login(username='user1', password='Password123!')
        response = self.client.get(reverse('tasks:dashboard'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'User 1 Task')

    def test_dashboard_recent_tasks_only_pending(self):
        """Recent Tasks must only include pending tasks and exclude completed tasks."""
        self.client.login(username='user1', password='Password123!')

        # Create a completed task
        Task.objects.create(
            user=self.user1,
            title='Completed Task Should Not Appear',
            completed=True,
            due_date=timezone.now().date()
        )

        response = self.client.get(reverse('tasks:dashboard'))
        self.assertEqual(response.status_code, 200)
        recent_tasks = response.context['recent_tasks']
        self.assertIn(self.task1, recent_tasks)
        self.assertFalse(any(t.completed for t in recent_tasks))
        self.assertNotContains(response, 'Completed Task Should Not Appear')

    def test_dashboard_recent_tasks_empty_state_message(self):
        """When there are no pending tasks, the exact empty-state message should be displayed."""
        self.client.login(username='user1', password='Password123!')
        # Mark all tasks completed
        Task.objects.filter(user=self.user1).update(completed=True)

        response = self.client.get(reverse('tasks:dashboard'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "No pending tasks available. You're all caught up!")

    def test_create_task(self):
        self.client.login(username='user1', password='Password123!')
        response = self.client.post(reverse('tasks:task_create'), {
            'title': 'New Task',
            'description': 'Brand new task',
            'priority': 'medium',
            'due_date': str(timezone.now().date()),
        })
        self.assertEqual(response.status_code, 302)
        self.assertTrue(Task.objects.filter(title='New Task', user=self.user1).exists())

    def test_create_task_ajax(self):
        self.client.login(username='user1', password='Password123!')
        response = self.client.post(
            reverse('tasks:task_create'),
            {'title': 'AJAX Task', 'priority': 'low'},
            headers={'X-Requested-With': 'XMLHttpRequest'}
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data['success'])

    def test_toggle_task(self):
        self.client.login(username='user1', password='Password123!')
        self.assertFalse(self.task1.completed)

        response = self.client.post(reverse('tasks:task_toggle', args=[self.task1.id]))
        self.assertEqual(response.status_code, 302)
        self.task1.refresh_from_db()
        self.assertTrue(self.task1.completed)

        # Toggle with AJAX and explicit payload
        response_ajax = self.client.post(
            reverse('tasks:task_toggle', args=[self.task1.id]),
            {'completed': False},
            content_type='application/json',
            headers={'X-Requested-With': 'XMLHttpRequest'}
        )
        self.assertEqual(response_ajax.status_code, 200)
        self.task1.refresh_from_db()
        self.assertFalse(self.task1.completed)

    def test_bulk_toggle_task(self):
        self.client.login(username='user1', password='Password123!')
        task2 = Task.objects.create(user=self.user1, title='Task 2', completed=False)

        # Bulk mark completed
        response = self.client.post(
            reverse('tasks:task_bulk_toggle'),
            {'task_ids': [self.task1.id, task2.id], 'completed': True},
            content_type='application/json',
            headers={'X-Requested-With': 'XMLHttpRequest'}
        )
        self.assertEqual(response.status_code, 200)
        self.task1.refresh_from_db()
        task2.refresh_from_db()
        self.assertTrue(self.task1.completed)
        self.assertTrue(task2.completed)

        # Bulk mark pending
        response_pending = self.client.post(
            reverse('tasks:task_bulk_toggle'),
            {'task_ids': [self.task1.id, task2.id], 'completed': False},
            content_type='application/json',
            headers={'X-Requested-With': 'XMLHttpRequest'}
        )
        self.assertEqual(response_pending.status_code, 200)
        self.task1.refresh_from_db()
        task2.refresh_from_db()
        self.assertFalse(self.task1.completed)
        self.assertFalse(task2.completed)

    def test_delete_task(self):
        self.client.login(username='user1', password='Password123!')
        response = self.client.post(reverse('tasks:task_delete', args=[self.task1.id]))
        self.assertEqual(response.status_code, 302)
        self.assertFalse(Task.objects.filter(id=self.task1.id).exists())

    def test_user_data_isolation(self):
        """User 2 should NOT be able to view, edit, toggle, or delete User 1's tasks."""
        self.client.login(username='user2', password='Password123!')

        # Dashboard of User 2 should not contain User 1's tasks
        res = self.client.get(reverse('tasks:dashboard'))
        self.assertNotContains(res, 'User 1 Task')

        # User 2 attempting to toggle User 1's task should 404
        toggle_res = self.client.post(reverse('tasks:task_toggle', args=[self.task1.id]))
        self.assertEqual(toggle_res.status_code, 404)

        # User 2 attempting to delete User 1's task should 404
        delete_res = self.client.post(reverse('tasks:task_delete', args=[self.task1.id]))
        self.assertEqual(delete_res.status_code, 404)

        # User 2 attempting to edit User 1's task should 404
        edit_res = self.client.post(reverse('tasks:task_edit', args=[self.task1.id]), {'title': 'Hacked'})
        self.assertEqual(edit_res.status_code, 404)

    def test_search_and_filter(self):
        self.client.login(username='user1', password='Password123!')
        Task.objects.create(user=self.user1, title='Clean desk', priority='low', completed=True)

        # Default task list GET (no query params)
        res_default = self.client.get(reverse('tasks:task_list'))
        self.assertEqual(res_default.status_code, 200)

        # Search
        res = self.client.get(reverse('tasks:task_list') + '?search=desk')
        self.assertContains(res, 'Clean desk')
        self.assertNotContains(res, 'User 1 Task')

        # Filter by status
        res_completed = self.client.get(reverse('tasks:task_list') + '?status=completed')
        self.assertContains(res_completed, 'Clean desk')
        self.assertNotContains(res_completed, 'User 1 Task')

        # Filter by priority
        res_priority_all = self.client.get(reverse('tasks:task_list') + '?priority=all')
        self.assertEqual(res_priority_all.status_code, 200)

        res_priority_high = self.client.get(reverse('tasks:task_list') + '?priority=high')
        self.assertEqual(res_priority_high.status_code, 200)
        self.assertContains(res_priority_high, 'User 1 Task')
        self.assertNotContains(res_priority_high, 'Clean desk')

        # Filter by overdue
        overdue_task = Task.objects.create(
            user=self.user1,
            title='Old Late Task',
            priority='medium',
            completed=False,
            due_date=timezone.now().date() - timedelta(days=5)
        )
        res_overdue = self.client.get(reverse('tasks:task_list') + '?status=all&overdue=1')
        self.assertEqual(res_overdue.status_code, 200)
        self.assertContains(res_overdue, 'Old Late Task')
        self.assertNotContains(res_overdue, 'User 1 Task')

    def test_overdue_property(self):
        past_task = Task.objects.create(
            user=self.user1,
            title='Overdue Task',
            priority='high',
            completed=False,
            due_date=timezone.now().date() - timedelta(days=2)
        )
        self.assertTrue(past_task.is_overdue())

        past_task.completed = True
        past_task.save()
        self.assertFalse(past_task.is_overdue())

    def test_task_list_description_column(self):
        self.client.login(username='user1', password='Password123!')
        Task.objects.create(
            user=self.user1,
            title='Task without description',
            description='',
            priority='low',
            completed=False
        )

        res = self.client.get(reverse('tasks:task_list'))
        self.assertEqual(res.status_code, 200)
        self.assertContains(res, '>Description</th>')
        self.assertContains(res, 'class="task-desc-cell"')
        self.assertContains(res, 'class="task-desc-text"')
        self.assertContains(res, 'Description 1')
        self.assertContains(res, 'title="Description 1"')
        self.assertContains(res, '—')

    def test_dynamic_page_headers_across_modules(self):
        """Verify each sidebar module displays its corresponding title and description in the header."""
        self.client.login(username='user1', password='Password123!')
        modules = [
            (reverse('tasks:dashboard'), 'Dashboard', "Here's your productivity overview."),
            (reverse('tasks:task_list'), 'All Tasks', "Manage, edit, and track all your tasks."),
            (reverse('reports:report_dashboard'), 'Reports', "Track your productivity and task progress."),
            (reverse('accounts:profile'), 'Profile', "Manage your account settings."),
        ]
        for url, expected_title, expected_subtitle in modules:
            res = self.client.get(url)
            self.assertEqual(res.status_code, 200)
            self.assertContains(res, f"<h1>{expected_title}</h1>")
            self.assertContains(res, expected_subtitle)

    def test_task_grid_scroll_container_and_no_main_scrollbar(self):
        """Verify All Tasks page renders container classes for viewport-locked scrolling and sticky table headers."""
        self.client.login(username='user1', password='Password123!')
        res = self.client.get(reverse('tasks:task_list'))
        self.assertEqual(res.status_code, 200)
        self.assertContains(res, 'page-tasks')
        self.assertContains(res, 'tasks-view-container')
        self.assertContains(res, 'task-action-bar')
        self.assertContains(res, 'task-filters-card')
        self.assertContains(res, 'task-card-container')
        self.assertContains(res, 'task-card-body')
        self.assertContains(res, 'task-table-scroll-container')
        self.assertContains(res, 'task-table-footer')
        self.assertContains(res, 'position: sticky;')

    def test_notifications_requires_login(self):
        """Notification endpoint requires authentication."""
        res = self.client.get(reverse('tasks:notifications'))
        self.assertEqual(res.status_code, 302)

    def test_notifications_authenticated_classification_and_ordering(self):
        """
        Verify notification endpoint retrieves pending tasks with due dates,
        classifies them into Overdue, Due Today, and Upcoming, orders Overdue first,
        and excludes completed tasks or tasks without due dates.
        """
        today = timezone.now().date()
        # Clean existing tasks for user1
        Task.objects.filter(user=self.user1).delete()

        # 1. Overdue task
        t_overdue = Task.objects.create(
            user=self.user1,
            title='Overdue Task',
            priority='high',
            completed=False,
            due_date=today - timedelta(days=2)
        )
        # 2. Due Today task
        t_today = Task.objects.create(
            user=self.user1,
            title='Due Today Task',
            priority='medium',
            completed=False,
            due_date=today
        )
        # 3. Upcoming task
        t_upcoming = Task.objects.create(
            user=self.user1,
            title='Upcoming Task',
            priority='low',
            completed=False,
            due_date=today + timedelta(days=3)
        )
        # 4. Completed task with due date (should be EXCLUDED)
        Task.objects.create(
            user=self.user1,
            title='Completed Task',
            priority='high',
            completed=True,
            due_date=today - timedelta(days=1)
        )
        # 5. Pending task with NO due date (should be EXCLUDED)
        Task.objects.create(
            user=self.user1,
            title='No Due Date Task',
            priority='medium',
            completed=False,
            due_date=None
        )
        # 6. Other user's task (should be EXCLUDED)
        Task.objects.create(
            user=self.user2,
            title='User 2 Task',
            priority='high',
            completed=False,
            due_date=today - timedelta(days=1)
        )

        self.client.login(username='user1', password='Password123!')
        res = self.client.get(reverse('tasks:notifications'))
        self.assertEqual(res.status_code, 200)

        data = res.json()
        self.assertTrue(data['success'])
        self.assertEqual(data['count'], 3)
        self.assertEqual(data['overdue_count'], 1)
        self.assertEqual(data['due_today_count'], 1)
        self.assertEqual(data['upcoming_count'], 1)

        tasks = data['tasks']
        self.assertEqual(len(tasks), 3)

        # First task must be Overdue
        self.assertEqual(tasks[0]['id'], t_overdue.id)
        self.assertEqual(tasks[0]['title'], 'Overdue Task')
        self.assertEqual(tasks[0]['status_badge'], 'overdue')
        self.assertEqual(tasks[0]['status_label'], 'Overdue')
        self.assertEqual(tasks[0]['priority'], 'high')

        # Second task must be Due Today
        self.assertEqual(tasks[1]['id'], t_today.id)
        self.assertEqual(tasks[1]['title'], 'Due Today Task')
        self.assertEqual(tasks[1]['status_badge'], 'due_today')
        self.assertEqual(tasks[1]['status_label'], 'Due Today')

        # Third task must be Upcoming
        self.assertEqual(tasks[2]['id'], t_upcoming.id)
        self.assertEqual(tasks[2]['title'], 'Upcoming Task')
        self.assertEqual(tasks[2]['status_badge'], 'upcoming')
        self.assertEqual(tasks[2]['status_label'], 'Upcoming')

    def test_notifications_empty_state(self):
        """Notification endpoint returns empty list when user has no pending due-date tasks."""
        Task.objects.filter(user=self.user1).delete()
        self.client.login(username='user1', password='Password123!')
        res = self.client.get(reverse('tasks:notifications'))
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertTrue(data['success'])
        self.assertEqual(data['count'], 0)
        self.assertEqual(data['tasks'], [])

    def test_upcoming_task_reminder_email(self):
        """Verify upcoming task reminder email is sent with correct subject, HTML table, and no duplicates."""
        self.user1.email = 'user1@example.com'
        self.user1.save()
        today = timezone.now().date()
        Task.objects.filter(user=self.user1).delete()

        task = Task.objects.create(
            user=self.user1,
            title='Prepare Sprint Presentation',
            description='Finalize slide deck for review',
            priority='high',
            completed=False,
            due_date=today + timedelta(days=1)
        )

        mail.outbox.clear()
        stats = process_and_send_due_notifications()
        self.assertEqual(stats['upcoming_emails_sent'], 1)
        self.assertEqual(len(mail.outbox), 1)

        sent_email = mail.outbox[0]
        self.assertEqual(sent_email.subject, 'Task Due Date Reminder – Action Required')
        self.assertIn('user1@example.com', sent_email.to)
        self.assertIn('Prepare Sprint Presentation', sent_email.body)
        self.assertIn('Priority', sent_email.body)
        self.assertIn('Status', sent_email.body)
        self.assertIn('Due Date', sent_email.body)

        # Check HTML alternative table
        self.assertTrue(len(sent_email.alternatives) > 0)
        html_content = sent_email.alternatives[0][0]
        self.assertIn('No.', html_content)
        self.assertIn('Task Title', html_content)
        self.assertIn('Description', html_content)
        self.assertIn('Priority', html_content)
        self.assertIn('Status', html_content)
        self.assertIn('Due Date', html_content)

        # Verify task is flagged as sent
        task.refresh_from_db()
        self.assertTrue(task.upcoming_reminder_sent)
        self.assertIsNotNone(task.upcoming_reminder_sent_at)

        # Subsequent run must NOT send duplicate
        mail.outbox.clear()
        stats2 = process_and_send_due_notifications()
        self.assertEqual(stats2['upcoming_emails_sent'], 0)
        self.assertEqual(len(mail.outbox), 0)

    def test_overdue_task_alert_email(self):
        """Verify overdue task alert email has subject 'Overdue Task Alert – [Task Title]' and prevents duplicates."""
        self.user1.email = 'user1@example.com'
        self.user1.save()
        today = timezone.now().date()
        Task.objects.filter(user=self.user1).delete()

        task = Task.objects.create(
            user=self.user1,
            title='Submit Tax Report',
            description='Accounting documents submission',
            priority='high',
            completed=False,
            due_date=today - timedelta(days=1)
        )

        mail.outbox.clear()
        stats = process_and_send_due_notifications()
        self.assertEqual(stats['overdue_emails_sent'], 1)
        self.assertEqual(len(mail.outbox), 1)

        sent_email = mail.outbox[0]
        self.assertEqual(sent_email.subject, 'Overdue Task Alert – Submit Tax Report')
        self.assertIn('user1@example.com', sent_email.to)
        self.assertIn('Submit Tax Report', sent_email.body)

        task.refresh_from_db()
        self.assertTrue(task.overdue_alert_sent)
        self.assertIsNotNone(task.overdue_alert_sent_at)

        # Duplicate check
        mail.outbox.clear()
        stats2 = process_and_send_due_notifications()
        self.assertEqual(stats2['overdue_emails_sent'], 0)
        self.assertEqual(len(mail.outbox), 0)

    def test_completed_tasks_and_tasks_without_due_date_excluded(self):
        """Verify completed tasks or tasks without a due date never trigger notification emails."""
        self.user1.email = 'user1@example.com'
        self.user1.save()
        today = timezone.now().date()
        Task.objects.filter(user=self.user1).delete()

        # Completed task with overdue date
        Task.objects.create(
            user=self.user1,
            title='Completed Overdue Task',
            priority='medium',
            completed=True,
            due_date=today - timedelta(days=2)
        )
        # Completed task with upcoming date
        Task.objects.create(
            user=self.user1,
            title='Completed Upcoming Task',
            priority='low',
            completed=True,
            due_date=today + timedelta(days=1)
        )
        # Pending task with NO due date
        Task.objects.create(
            user=self.user1,
            title='Pending No Due Date Task',
            priority='high',
            completed=False,
            due_date=None
        )

        mail.outbox.clear()
        stats = process_and_send_due_notifications()
        self.assertEqual(stats['overdue_emails_sent'], 0)
        self.assertEqual(stats['upcoming_emails_sent'], 0)
        self.assertEqual(len(mail.outbox), 0)

    def test_management_command_send_task_reminders(self):
        """Verify the 'send_task_reminders' management command runs cleanly."""
        self.user1.email = 'user1@example.com'
        self.user1.save()
        today = timezone.now().date()
        Task.objects.filter(user=self.user1).delete()

        Task.objects.create(
            user=self.user1,
            title='Command Test Task',
            priority='low',
            completed=False,
            due_date=today + timedelta(days=1)
        )

        mail.outbox.clear()
        call_command('send_task_reminders')
        self.assertEqual(len(mail.outbox), 1)






