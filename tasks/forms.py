from django import forms
from .models import Task,Project, TaskFile,Comment,ProfilePhoto
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm


class TaskFileForm(forms.ModelForm):
    class Meta:
        model = TaskFile
        fields = ['file']


class TaskForm(forms.ModelForm):

    class Meta:
        model = Task
        fields = ['name', 'description' ,'deadline', 'priority',"status",'image', 'project']


class ProjectForm(forms.ModelForm):
    tasks = forms.ModelMultipleChoiceField(
        queryset=Task.objects.none(),  # Порожній queryset спочатку
        widget=forms.CheckboxSelectMultiple,  # Відображати як чекбокси
        required=False,  # Це поле не обов'язкове
    )
    participants = forms.ModelMultipleChoiceField(
        queryset=User.objects.all(),  # Вибір усіх користувачів
        widget=forms.CheckboxSelectMultiple,  # Відображати як чекбокси
        required=False,  # Це поле не обов'язкове
    )
    class Meta:
        model = Project
        fields = ['name','description','deadline','participants', 'tasks']

    def __init__(self, *args, **kwargs):
        owner = kwargs.pop('owner', None)
        super().__init__(*args, **kwargs)
        # Вибираємо тільки ті завдання, які не мають проекту
        self.fields['tasks'].queryset = Task.objects.filter(project__isnull=True)

        if owner:
            # Вилучаємо власника з queryset для учасників
            self.fields['participants'].queryset = User.objects.exclude(id=owner.id)

        if self.instance.pk:  # Якщо проект вже існує (редагування)
            self.fields['tasks'].queryset = Task.objects.all()  # Отримуємо всі завдання
            self.fields['tasks'].initial = self.instance.tasks.all()  # Встановлюємо поточні завдання проекту


class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ['text']

class CustomUserCreationForm(UserCreationForm):
    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email']


class ProfilePhotoForm(forms.ModelForm):
    class Meta:
        model = ProfilePhoto
        fields = ['photo']