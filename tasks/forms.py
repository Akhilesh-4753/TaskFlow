from django import forms
from .models import Task


class TaskForm(forms.ModelForm):
    """ModelForm for creating and editing tasks."""

    title = forms.CharField(
        max_length=200,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter task title',
            'maxlength': '200',
            'id': 'id_task_title',
        }),
        label='Title'
    )
    description = forms.CharField(
        required=False,
        max_length=2000,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'placeholder': 'Enter task description',
            'rows': 4,
            'maxlength': '2000',
            'id': 'id_task_description',
        }),
        label='Description'
    )
    priority = forms.ChoiceField(
        choices=Task.PRIORITY_CHOICES,
        initial='medium',
        widget=forms.Select(attrs={
            'class': 'form-select',
            'id': 'id_task_priority',
        }),
        label='Priority'
    )
    due_date = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date',
            'id': 'id_task_due_date',
        }),
        label='Due Date'
    )
    completed = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input',
            'id': 'id_task_completed',
        }),
        label='Mark as completed'
    )

    class Meta:
        model = Task
        fields = ('title', 'description', 'priority', 'due_date', 'completed')

