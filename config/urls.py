"""
URL configuration for TaskFlow project.
"""

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('accounts.urls', namespace='accounts')),
    path('tasks/', include('tasks.urls', namespace='tasks')),
    path('reports/', include('reports.urls', namespace='reports')),
    path('assistant/', include('assistant.urls', namespace='assistant')),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

