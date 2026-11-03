from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta
from tasks.models import Task


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



