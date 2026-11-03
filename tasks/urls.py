from django.urls import path
from . import views

app_name = 'tasks'

urlpatterns = [
    path('', views.dashboard_view, name='dashboard'),
    path('list/', views.task_list_view, name='task_list'),
    path('create/', views.task_create_view, name='task_create'),
    path('<int:pk>/edit/', views.task_edit_view, name='task_edit'),
    path('<int:pk>/delete/', views.task_delete_view, name='task_delete'),
    path('<int:pk>/toggle/', views.task_toggle_view, name='task_toggle'),
    path('bulk-toggle/', views.task_bulk_toggle_view, name='task_bulk_toggle'),
    path('suggest/', views.task_suggest_ai_view, name='task_suggest'),
]

