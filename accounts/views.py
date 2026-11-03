from django.shortcuts import render, redirect
from django.contrib.auth import login, logout, authenticate, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth.models import User
from .forms import SignupForm, LoginForm, ProfileUpdateForm, PasswordChangeForm, ProfileAvatarForm
from .models import Profile


def signup_view(request):
    """Handle user registration."""
    if request.user.is_authenticated:
        return redirect('tasks:dashboard')

    if request.method == 'POST':
        form = SignupForm(request.POST)
        if form.is_valid():
            user = form.save()
            # Create a profile for the new user
            Profile.objects.get_or_create(user=user)
            login(request, user)
            messages.success(request, f'Welcome to TaskFlow, {user.first_name or user.username}! 🎉')
            return redirect('tasks:dashboard')
        else:
            messages.error(request, 'Please fix the errors below to create your account.')
    else:
        form = SignupForm()

    return render(request, 'accounts/signup.html', {'form': form})


def login_view(request):
    """Handle user login."""
    if request.user.is_authenticated:
        return redirect('tasks:dashboard')

    if request.method == 'POST':
        form = LoginForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            remember_me = form.cleaned_data.get('remember_me', False)
            login(request, user)
            if remember_me:
                # Maintain extended session (30 days) when Remember Me is checked
                request.session.set_expiry(30 * 24 * 60 * 60)
            else:
                # Expire session on browser close when Remember Me is unchecked
                request.session.set_expiry(0)
            # Create profile if missing (for existing users)
            Profile.objects.get_or_create(user=user)
            messages.success(request, f'Welcome back, {user.first_name or user.username}! 👋')
            next_url = request.POST.get('next') or request.GET.get('next') or 'tasks:dashboard'
            if not next_url or str(next_url).strip() == '':
                next_url = 'tasks:dashboard'
            return redirect(next_url)
        else:
            messages.error(request, 'Please check your login credentials and try again.')
    else:
        form = LoginForm(request)

    return render(request, 'accounts/login.html', {'form': form})


def logout_view(request):
    """Handle user logout."""
    logout(request)
    messages.info(request, 'You have been logged out successfully.')
    return redirect('accounts:login')


@login_required
def profile_view(request):
    """Display and update user profile, avatar, and password."""
    user = request.user
    profile, _ = Profile.objects.get_or_create(user=user)

    profile_form = ProfileUpdateForm(instance=user)
    avatar_form = ProfileAvatarForm(instance=profile)
    password_form = PasswordChangeForm(user=user)

    if request.method == 'POST':
        action = request.POST.get('action')

        if action == 'update_profile':
            profile_form = ProfileUpdateForm(request.POST, instance=user)
            avatar_form = ProfileAvatarForm(request.POST, request.FILES, instance=profile)

            # Handle optional avatar removal
            if request.POST.get('remove_avatar') == '1' and profile.avatar:
                profile.avatar.delete(save=False)
                profile.avatar = None
                profile.save()

            if profile_form.is_valid() and avatar_form.is_valid():
                profile_form.save()
                if 'avatar' in request.FILES:
                    avatar_form.save()
                messages.success(request, 'Profile updated successfully.')
                return redirect('accounts:profile')
            else:
                messages.error(request, 'Please correct the errors below.')

        elif action == 'remove_avatar':
            if profile.avatar:
                profile.avatar.delete(save=False)
                profile.avatar = None
                profile.save()
                messages.success(request, 'Profile picture removed successfully.')
            return redirect('accounts:profile')

        elif action == 'change_password':
            password_form = PasswordChangeForm(user=user, data=request.POST)
            if password_form.is_valid():
                new_password = password_form.cleaned_data['new_password1']
                user.set_password(new_password)
                user.save()
                update_session_auth_hash(request, user)  # Keep user logged in
                messages.success(request, 'Password changed successfully.')
                return redirect('accounts:profile')
            else:
                messages.error(request, 'Please correct the errors below.')

    context = {
        'profile_form': profile_form,
        'avatar_form': avatar_form,
        'password_form': password_form,
        'profile': profile,
        'active_page': 'profile',
    }
    return render(request, 'accounts/profile.html', context)

