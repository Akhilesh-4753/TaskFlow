import os
import uuid
from django.db import models
from django.contrib.auth.models import User


def avatar_upload_path(instance, filename):
    """Generate a secure unique file path for uploaded avatars."""
    ext = filename.split('.')[-1].lower() if '.' in filename else 'jpg'
    unique_name = f"{uuid.uuid4().hex}.{ext}"
    return os.path.join('avatars', unique_name)


class Profile(models.Model):
    """Extended profile information linked one-to-one with Django's User model."""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    avatar = models.ImageField(upload_to=avatar_upload_path, blank=True, null=True)
    bio = models.TextField(blank=True, max_length=500)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Profile of {self.user.username}"

    def get_initials(self):
        """Return user initials for avatar display."""
        name = self.user.get_full_name()
        if name:
            parts = name.split()
            return ''.join(p[0].upper() for p in parts[:2])
        return self.user.username[:2].upper()

    @property
    def has_avatar(self):
        return bool(self.avatar and hasattr(self.avatar, 'url'))


