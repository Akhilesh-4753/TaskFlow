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

        # Search
        res = self.client.get(reverse('tasks:task_list') + '?search=desk')
        self.assertContains(res, 'Clean desk')
        self.assertNotContains(res, 'User 1 Task')

        # Filter by status
        res_completed = self.client.get(reverse('tasks:task_list') + '?status=completed')
        self.assertContains(res_completed, 'Clean desk')
        self.assertNotContains(res_completed, 'User 1 Task')

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

