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

    def test_login_with_email(self):
        response = self.client.post(reverse('accounts:login'), {
            'username': 'john@example.com',
            'password': 'StrongPassword123!',
        })
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('tasks:dashboard'))

    def test_login_case_insensitive(self):
        response = self.client.post(reverse('accounts:login'), {
            'username': 'JohnDoe',
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

    def test_avatar_upload_valid_image(self):
        import io
        from PIL import Image
        from django.core.files.uploadedfile import SimpleUploadedFile

        self.client.login(username='johndoe', password='StrongPassword123!')

        # Generate a small 100x100 RGB image
        file_io = io.BytesIO()
        image = Image.new('RGB', (100, 100), color='blue')
        image.save(file_io, format='JPEG')
        file_io.seek(0)

        avatar_file = SimpleUploadedFile(
            name='test_avatar.jpg',
            content=file_io.read(),
            content_type='image/jpeg'
        )

        response = self.client.post(reverse('accounts:profile'), {
            'action': 'update_profile',
            'first_name': 'John',
            'last_name': 'Doe',
            'email': 'john@example.com',
            'avatar': avatar_file,
        })
        self.assertEqual(response.status_code, 302)
        self.profile.refresh_from_db()
        self.assertTrue(bool(self.profile.avatar))
        self.assertTrue(self.profile.avatar.url.startswith('/media/avatars/'))

        # Check that topbar renders the avatar img tag
        dashboard_res = self.client.get(reverse('tasks:dashboard'))
        self.assertContains(dashboard_res, self.profile.avatar.url)

    def test_avatar_upload_invalid_file_type(self):
        from django.core.files.uploadedfile import SimpleUploadedFile

        self.client.login(username='johndoe', password='StrongPassword123!')
        fake_file = SimpleUploadedFile(
            name='evil_script.pdf',
            content=b'not an image content',
            content_type='application/pdf'
        )

        response = self.client.post(reverse('accounts:profile'), {
            'action': 'update_profile',
            'first_name': 'John',
            'last_name': 'Doe',
            'email': 'john@example.com',
            'avatar': fake_file,
        })
        self.assertEqual(response.status_code, 200)
        self.profile.refresh_from_db()
        self.assertFalse(bool(self.profile.avatar))
        self.assertTrue('Upload a valid image' in response.content.decode() or 'Unsupported image format' in response.content.decode())

    def test_avatar_remove(self):
        import io
        from PIL import Image
        from django.core.files.uploadedfile import SimpleUploadedFile

        self.client.login(username='johndoe', password='StrongPassword123!')
        file_io = io.BytesIO()
        image = Image.new('RGB', (50, 50), color='green')
        image.save(file_io, format='PNG')
        file_io.seek(0)

        avatar_file = SimpleUploadedFile(name='remove_test.png', content=file_io.read(), content_type='image/png')
        self.profile.avatar = avatar_file
        self.profile.save()
        self.assertTrue(bool(self.profile.avatar))

        # Remove avatar
        response = self.client.post(reverse('accounts:profile'), {
            'action': 'remove_avatar'
        })
        self.assertEqual(response.status_code, 302)
        self.profile.refresh_from_db()
        self.assertFalse(bool(self.profile.avatar))

    def test_profile_two_column_layout(self):
        """Verify the Profile page renders a two-column grid layout containing both Edit Profile and Change Password cards."""
        self.client.login(username='johndoe', password='StrongPassword123!')
        res = self.client.get(reverse('accounts:profile'))
        self.assertEqual(res.status_code, 200)
        self.assertContains(res, 'class="profile-grid"')
        self.assertContains(res, 'Edit Profile')
        self.assertContains(res, 'Change Password')
        self.assertContains(res, 'Password Security')
        self.assertContains(res, 'Save Changes')
        self.assertContains(res, 'Update Password')



