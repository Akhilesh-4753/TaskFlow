from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth import password_validation


class SignupForm(UserCreationForm):
    """Custom signup form with full name and email fields."""
    first_name = forms.CharField(
        max_length=50,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter your full name',
            'autocomplete': 'given-name',
        }),
        label='Full Name'
    )
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter your email',
            'autocomplete': 'email',
        }),
        label='Email'
    )
    username = forms.CharField(
        max_length=150,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Choose a username (optional)',
            'autocomplete': 'username',
        }),
        label='Username'
    )
    password1 = forms.CharField(
        label='Password',
        strip=False,
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Create a password',
            'autocomplete': 'new-password',
            'id': 'id_password1',
        }),
        help_text=password_validation.password_validators_help_text_html(),
    )
    password2 = forms.CharField(
        label='Confirm Password',
        strip=False,
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Confirm your password',
            'autocomplete': 'new-password',
            'id': 'id_password2',
        }),
    )
    agree_terms = forms.BooleanField(
        required=False,
        label='I agree to the Terms of Service and Privacy Policy',
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
    )

    class Meta:
        model = User
        fields = ('first_name', 'username', 'email', 'password1', 'password2', 'agree_terms')

    def clean_username(self):
        username = self.cleaned_data.get('username', '').strip()
        if not username:
            email = self.cleaned_data.get('email') or self.data.get('email', '')
            email = email.strip().lower()
            if email:
                import re
                base = email.split('@')[0][:30]
                base = re.sub(r'[^\w.@+-]', '_', base)
                candidate = base
                counter = 1
                while User.objects.filter(username__iexact=candidate).exists():
                    candidate = f"{base}_{counter}"
                    counter += 1
                username = candidate
        else:
            if User.objects.filter(username__iexact=username).exists():
                raise forms.ValidationError('A user with this username already exists.')
        return username

    def clean_email(self):
        email = self.cleaned_data.get('email', '').strip().lower()
        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError('A user with this email already exists.')
        return email

    def save(self, commit=True):
        user = super().save(commit=False)
        # Split full name into first/last
        full_name = self.cleaned_data.get('first_name', '').strip()
        parts = full_name.split(' ', 1)
        user.first_name = parts[0]
        user.last_name = parts[1] if len(parts) > 1 else ''
        user.email = self.cleaned_data.get('email', '').lower()
        if commit:
            user.save()
        return user


class LoginForm(AuthenticationForm):
    """Custom login form with Bootstrap styling supporting both username and email (case-insensitive)."""
    username = forms.CharField(
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter your email or username',
            'autocomplete': 'username',
        }),
        label='Email or Username'
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter your password',
            'autocomplete': 'current-password',
            'id': 'id_login_password',
        }),
        label='Password'
    )
    remember_me = forms.BooleanField(
        required=False,
        label='Remember me',
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )

    def clean(self):
        username_or_email = self.cleaned_data.get('username', '').strip()
        password = self.cleaned_data.get('password')

        if username_or_email and password:
            from django.db.models import Q
            from django.contrib.auth import authenticate
            user_obj = User.objects.filter(
                Q(username__iexact=username_or_email) | Q(email__iexact=username_or_email)
            ).first()

            if user_obj:
                self.user_cache = authenticate(
                    self.request,
                    username=user_obj.username,
                    password=password
                )
                if self.user_cache is None and password != password.strip():
                    self.user_cache = authenticate(
                        self.request,
                        username=user_obj.username,
                        password=password.strip()
                    )
            else:
                self.user_cache = authenticate(
                    self.request,
                    username=username_or_email,
                    password=password
                )

            if self.user_cache is None:
                raise self.get_invalid_login_error()
            else:
                self.confirm_login_allowed(self.user_cache)

        return self.cleaned_data


class ProfileUpdateForm(forms.ModelForm):
    """Form for updating user profile information."""
    first_name = forms.CharField(
        max_length=50, required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'First name'})
    )
    last_name = forms.CharField(
        max_length=50, required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Last name'})
    )
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Email address'})
    )

    class Meta:
        model = User
        fields = ('first_name', 'last_name', 'email')

    def clean_email(self):
        email = self.cleaned_data.get('email', '').lower()
        qs = User.objects.filter(email=email).exclude(pk=self.instance.pk)
        if qs.exists():
            raise forms.ValidationError('This email is already in use.')
        return email


class ProfileAvatarForm(forms.ModelForm):
    """Form for updating profile image with size, extension, and content validation."""
    avatar = forms.ImageField(
        required=False,
        widget=forms.FileInput(attrs={
            'class': 'form-control',
            'id': 'avatarFileInput',
            'accept': 'image/jpeg,image/png,image/webp,image/gif'
        })
    )

    class Meta:
        from .models import Profile
        model = Profile
        fields = ('avatar',)

    def clean_avatar(self):
        avatar = self.cleaned_data.get('avatar')
        if not avatar:
            return avatar

        # File size validation (Max 5MB)
        max_size_mb = 5
        if avatar.size > max_size_mb * 1024 * 1024:
            raise forms.ValidationError(
                f'Image file size must not exceed {max_size_mb} MB. (Uploaded: {avatar.size / (1024 * 1024):.1f} MB)'
            )

        # File extension validation
        import os
        ext = os.path.splitext(avatar.name)[1].lower()
        allowed_extensions = ['.jpg', '.jpeg', '.png', '.webp', '.gif']
        if ext not in allowed_extensions:
            raise forms.ValidationError(
                'Unsupported image format. Allowed formats: JPG, PNG, WEBP, GIF.'
            )

        # Verify image using Pillow
        from PIL import Image
        try:
            img = Image.open(avatar)
            img.verify()
        except Exception:
            raise forms.ValidationError('The uploaded file is not a valid or readable image.')

        return avatar



class PasswordChangeForm(forms.Form):
    """Form for changing user password."""
    current_password = forms.CharField(
        label='Current Password',
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Current password'})
    )
    new_password1 = forms.CharField(
        label='New Password',
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'New password'})
    )
    new_password2 = forms.CharField(
        label='Confirm New Password',
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Confirm new password'})
    )

    def __init__(self, user, *args, **kwargs):
        self.user = user
        super().__init__(*args, **kwargs)

    def clean_current_password(self):
        pw = self.cleaned_data.get('current_password')
        if not self.user.check_password(pw):
            raise forms.ValidationError('Current password is incorrect.')
        return pw

    def clean(self):
        cleaned_data = super().clean()
        p1 = cleaned_data.get('new_password1')
        p2 = cleaned_data.get('new_password2')
        if p1 and p2 and p1 != p2:
            raise forms.ValidationError('New passwords do not match.')
        if p1:
            password_validation.validate_password(p1, self.user)
        return cleaned_data

