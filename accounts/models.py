from django.db import models
from django.contrib.auth.models import User

# accounts/models.py
# We extend the built-in User model using a Profile model.

class Profile(models.Model):
    """Extended profile information linked one-to-one with Django's User model."""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
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

