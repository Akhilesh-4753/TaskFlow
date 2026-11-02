from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from accounts.models import Profile


class AccountsTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='johndoe',
            email='john@example.com',
            password='StrongPassword123!',
            first_name='John',
            last_name='Doe'
        )
        self.profile = Profile.objects.create(user=self.user)

    def test_signup_successful(self):
        response = self.client.post(reverse('accounts:signup'), {
            'first_name': 'Jane Doe',
            'username': 'janedoe',
            'email': 'jane@example.com',
            'password1': 'AnotherStrong123!',
            'password2': 'AnotherStrong123!',
            'agree_terms': 'on',
        })
        self.assertEqual(response.status_code, 302)
        self.assertTrue(User.objects.filter(username='janedoe').exists())
        self.assertTrue(Profile.objects.filter(user__username='janedoe').exists())

    def test_signup_duplicate_email(self):
        response = self.client.post(reverse('accounts:signup'), {
            'first_name': 'John Clone',
            'username': 'johnclone',
            'email': 'john@example.com',  # Duplicate email
            'password1': 'AnotherStrong123!',
            'password2': 'AnotherStrong123!',
            'agree_terms': 'on',
        })
        self.assertEqual(response.status_code, 200)
        self.assertFalse(User.objects.filter(username='johnclone').exists())

    def test_signup_password_mismatch(self):
        response = self.client.post(reverse('accounts:signup'), {
            'first_name': 'Mismatch User',
            'username': 'mismatch',
            'email': 'mismatch@example.com',
            'password1': 'Password123!',
            'password2': 'DifferentPassword123!',
            'agree_terms': 'on',
        })
        self.assertEqual(response.status_code, 200)
        self.assertFalse(User.objects.filter(username='mismatch').exists())

    def test_login_successful(self):
        response = self.client.post(reverse('accounts:login'), {
            'username': 'johndoe',
            'password': 'StrongPassword123!',
        })
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('tasks:dashboard'))

    def test_login_invalid_password(self):
        response = self.client.post(reverse('accounts:login'), {
            'username': 'johndoe',
            'password': 'WrongPassword!',
        })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Please enter a correct username and password')

    def test_logout(self):
        self.client.login(username='johndoe', password='StrongPassword123!')
        response = self.client.post(reverse('accounts:logout'))
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('accounts:login'))

    def test_profile_requires_login(self):
        response = self.client.get(reverse('accounts:profile'))
        self.assertEqual(response.status_code, 302)

    def test_profile_update(self):
        self.client.login(username='johndoe', password='StrongPassword123!')
        response = self.client.post(reverse('accounts:profile'), {
            'action': 'update_profile',
            'first_name': 'Johnny',
            'last_name': 'Doeman',
            'email': 'johnny@example.com',
        })
        self.assertEqual(response.status_code, 302)
        self.user.refresh_from_db()
        self.assertEqual(self.user.first_name, 'Johnny')
        self.assertEqual(self.user.email, 'johnny@example.com')

