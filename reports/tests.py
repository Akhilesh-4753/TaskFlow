from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta
from tasks.models import Task


class ReportsTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='reportuser', password='Password123!')

    def test_reports_requires_login(self):
        response = self.client.get(reverse('reports:report_dashboard'))
        self.assertEqual(response.status_code, 302)

    def test_reports_with_zero_tasks(self):
        self.client.login(username='reportuser', password='Password123!')
        response = self.client.get(reverse('reports:report_dashboard'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['total'], 0)
        self.assertEqual(response.context['completion_rate'], 0)

    def test_reports_calculations(self):
        self.client.login(username='reportuser', password='Password123!')
        # 1 completed, 1 pending (not overdue), 1 overdue
        Task.objects.create(user=self.user, title='T1', completed=True, priority='low')
        Task.objects.create(
            user=self.user, title='T2', completed=False, priority='medium',
            due_date=timezone.now().date() + timedelta(days=5)
        )
        Task.objects.create(
            user=self.user, title='T3', completed=False, priority='high',
            due_date=timezone.now().date() - timedelta(days=2)
        )

        response = self.client.get(reverse('reports:report_dashboard'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['total'], 3)
        self.assertEqual(response.context['completed'], 1)
        self.assertEqual(response.context['pending'], 2)
        self.assertEqual(response.context['overdue_count'], 1)
        # 1/3 * 100 = 33.3%
        self.assertEqual(response.context['completion_rate'], 33.3)

