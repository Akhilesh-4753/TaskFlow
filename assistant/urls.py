from django.urls import path
from . import views

app_name = 'assistant'

urlpatterns = [
    path('chat/', views.chat_view, name='chat'),
    path('suggest/', views.suggest_description_view, name='suggest'),
]

