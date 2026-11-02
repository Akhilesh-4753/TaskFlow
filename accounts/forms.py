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
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Choose a username',
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
        required=True,
        label='I agree to the Terms of Service and Privacy Policy',
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        error_messages={'required': 'You must agree to the terms and privacy policy.'}
    )

    class Meta:
        model = User
        fields = ('first_name', 'username', 'email', 'password1', 'password2', 'agree_terms')

    def clean_email(self):
        email = self.cleaned_data.get('email', '').lower()
        if User.objects.filter(email=email).exists():
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
    """Custom login form with Bootstrap styling."""
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

