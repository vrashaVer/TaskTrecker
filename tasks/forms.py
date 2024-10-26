from django import forms
from .models import Task,Project, TaskFile,Comment,ProfilePhoto,Friend
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from django.core.exceptions import ValidationError
from datetime import date


class TaskFileForm(forms.ModelForm):
    class Meta:
        model = TaskFile
        fields = ['file']


class TaskForm(forms.ModelForm):

    class Meta:
        model = Task
        fields = ['name', 'description' ,'deadline', 'priority',"status",'image', 'project']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),  # Додаємо клас до поля назви
            'description': forms.Textarea(attrs={'class': 'form-control'}),
            'deadline': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'priority': forms.Select(attrs={'class': 'form-control'}),
            'status': forms.Select(attrs={'class': 'form-control'}),
            'image': forms.ClearableFileInput(attrs={'class': 'form-control'}),
            'project': forms.Select(attrs={'class': 'form-control'}),
        }

    def clean_deadline(self):
        deadline = self.cleaned_data.get('deadline')
        if deadline and deadline < date.today():
            raise ValidationError("The deadline cannot be in the past.")
        return deadline

    def clean_name(self):
        name = self.cleaned_data.get('name')
        if len(name) < 3:
            raise ValidationError("The task name must be at least 3 characters long.")
        return name

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
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),  # Додаємо клас до поля назви
            'description': forms.Textarea(attrs={'class': 'form-control'}),
            'deadline': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        owner = kwargs.pop('owner', None)
        super().__init__(*args, **kwargs)
        # Вибираємо тільки ті завдання, які не мають проекту
        if self.instance.pk:  # Якщо це редагування проекту
            self.fields['tasks'].queryset = Task.objects.filter(
                project__isnull=True
            ) | Task.objects.filter(project=self.instance)
            self.fields['tasks'].initial = self.instance.tasks.all()
        else:  # Для створення нового проекту
            self.fields['tasks'].queryset = Task.objects.filter(project__isnull=True)

        if owner:
            # Вилучаємо власника з queryset для учасників
            friends = Friend.objects.filter(user=owner).values_list('friend', flat=True)
            self.fields['participants'].queryset = User.objects.filter(id__in=friends).exclude(id=owner.id)
           

    def clean_name(self):
        name = self.cleaned_data.get('name')
        if len(name) > 100:  # Перевірка на максимальну довжину
            raise ValidationError("Назва проєкту не повинна перевищувати 100 символів.")
        if len(name) < 3:  # Перевірка на мінімальну довжину
            raise ValidationError("Назва проєкту повинна містити не менше 3 символів.")
        return name

    def clean_deadline(self):
        deadline = self.cleaned_data.get('deadline')
        if deadline and deadline < date.today():
            raise ValidationError("Термін не може бути в минулому.")
        return deadline   
    


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