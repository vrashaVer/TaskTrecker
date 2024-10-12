from django.views.generic import TemplateView
from django.views.generic import ListView, DetailView, UpdateView, DeleteView, CreateView
from django.shortcuts import render, get_object_or_404
from django.urls import reverse_lazy, reverse
from .models import Task, Project
from datetime import datetime, timedelta
from .forms import TaskForm, ProjectForm
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.views import LoginView, LogoutView
from django.db.models import Q
from django import forms
from django.views import View
from django.http import HttpResponseRedirect


class HomePageView(TemplateView):
    template_name = 'tasks/home.html'



class TaskListView(ListView):
    model = Task
    template_name = 'tasks/tasks_list.html'
    context_object_name = 'tasks'
    
    def get_queryset(self):
        if self.request.user.is_authenticated:
            queryset = Task.objects.filter(owner=self.request.user)

            query = self.request.GET.get('search')
            if query:
                queryset = queryset.filter(name__icontains=query)
        else:
            queryset = Task.objects.none()
       
        
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.request.user.is_authenticated:
            upcoming_deadline = datetime.now() + timedelta(days=3)
            context['urgent_tasks'] = Task.objects.filter(owner=self.request.user,
                                                        deadline__lte=upcoming_deadline
                                                        ).order_by('deadline')
        else:
            context['urgent_tasks'] = Task.objects.none()

        return context


class TaskDetailView(DetailView):
    model = Task
    template_name = 'tasks/task_detail.html'
    context_object_name = 'task'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['next'] = self.request.GET.get('next')  # Додаємо параметр next в контекст
        return context

class TaskEditView(UpdateView):
    model = Task
    form_class = TaskForm
    template_name = 'tasks/update_task.html'  # Шаблон для редагування завдання

    def get_object(self, queryset=None):
        # Отримуємо завдання за ID
        return get_object_or_404(Task, id=self.kwargs['pk'])

    def get_success_url(self):
        # Перенаправляємо на деталі завдання після успішного редагування
        return reverse_lazy('task_detail', kwargs={'pk': self.object.id})

    def form_valid(self, form):
        # Зберігаємо старе значення проекту
        old_project = self.object.project

        # Зберігаємо нові дані форми
        response = super().form_valid(form)

        # Якщо завдання перенесене в інший проект або проект був видалений
        if old_project != form.cleaned_data['project']:
            # Якщо проект був знятий
            if form.cleaned_data['project'] is None:
                self.object.project = None
                self.object.save()

        return response

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['projects'] = Project.objects.all()  # Отримуємо всі проекти для вибору
        return context

class TaskDeleteView(LoginRequiredMixin, View):
    def get_object(self):
        # Отримуємо завдання за ID
        return get_object_or_404(Task, pk=self.kwargs['pk'])

    def post(self, request, *args, **kwargs):
        task = self.get_object()
        task.delete()  # Видаляємо завдання

        # Повертаємо на сторінку проекту або на список завдань
        next_url = request.POST.get('next')
        if next_url:
            return HttpResponseRedirect(next_url)
        return HttpResponseRedirect(reverse('tasks-list'))


class CustomLoginView(LoginView):
    template_name = 'tasks/registration/login.html'  # Шаблон для авторизації
    success_url = reverse_lazy('tasks-list')


class ProjectListView(ListView):
    model = Project
    template_name = 'tasks/projects_list.html'
    context_object_name = 'projects'
    paginate_by = 5
    
    def get_queryset(self):
        if self.request.user.is_authenticated:
            queryset = Project.objects.filter(
                owner=self.request.user
            ) | Project.objects.filter(
                participants=self.request.user
        )

            query = self.request.GET.get('search')
            if query:
                queryset = queryset.filter(name__icontains=query)
        else:
            queryset = Project.objects.none()
       
        
        return queryset.distinct()
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.request.user.is_authenticated:
            upcoming_deadline = datetime.now() + timedelta(days=3)
            context['upcoming_projects'] = Project.objects.filter(
                                                        Q(owner=self.request.user) | Q(participants=self.request.user),
                                                        deadline__lte=upcoming_deadline
                                                    ).order_by('deadline')
        else:
            context['upcoming_projects'] = Project.objects.none()

        
        return context
    

class ProjectCreateView(CreateView):
    model = Project
    form_class = ProjectForm  
    template_name = 'tasks/project_create.html'
    success_url = reverse_lazy('projects-list')  

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['owner'] = self.request.user  # Передаємо власника
        return kwargs

    def form_valid(self, form):
        form.instance.owner = self.request.user  
        response = super().form_valid(form)

        for task in form.cleaned_data['tasks']:
            task.project = self.object  # Прив'язуємо завдання до нового проекту
            task.save()

        return response
    

class TaskCreateView(LoginRequiredMixin, CreateView):
    model = Task
    form_class = TaskForm
    template_name = 'tasks/create_task.html'

    def get_form(self, *args, **kwargs):
        form = super().get_form(*args, **kwargs)
        project_id = self.kwargs.get('project_id')
        
        if project_id:
            project = get_object_or_404(Project, id=project_id)
            # Автоматично приховуємо поле проєкту та прив'язуємо завдання до проєкту
            form.fields['project'].widget = forms.HiddenInput()
            form.initial['project'] = project
        else:
            # Якщо немає project_id, користувач обирає проєкт вручну
            form.fields['project'].queryset = Project.objects.filter(
                Q(owner=self.request.user) | Q(participants=self.request.user)
            )
        return form

    def form_valid(self, form):
        form.instance.owner = self.request.user  # Встановлюємо власника завдання
        return super().form_valid(form)

    def get_success_url(self):
        project_id = self.kwargs.get('project_id')
        if project_id:
            # Якщо створюється з сторінки проєкту, перенаправляємо на сторінку деталей проєкту
            return reverse('project_detail', kwargs={'pk': project_id})
        else:
            # Якщо створюється зі сторінки завдань, перенаправляємо на список завдань
            return reverse_lazy('tasks-list')
        
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        project_id = self.kwargs.get('project_id')
        
        if project_id:
            context['project'] = get_object_or_404(Project, id=project_id)
        else:
            context['project'] = None  # Якщо немає project_id, встановлюємо None
        return context
        

class ProjectDetailView(DetailView):
    model = Project
    template_name = 'tasks/project_detail.html'
    context_object_name = 'project'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        project = self.get_object()  # Отримуємо поточний проєкт
        context['tasks'] = project.tasks.all()  # Додаємо в контекст завдання, прив'язані до проєкту
        return context
    

class ProjectUpdateView(LoginRequiredMixin, UpdateView):
    model = Project
    form_class = ProjectForm
    template_name = 'tasks/update_project.html'  # Шаблон для редагування проекту

    def get_object(self, queryset=None):
        # Отримуємо проект за ID
        return get_object_or_404(Project, id=self.kwargs['pk'])

    def get_success_url(self):
        # Перенаправляємо на деталі проекту після успішного редагування
        return reverse_lazy('project_detail', kwargs={'pk': self.object.id})
    def form_valid(self, form):
        # Отримуємо поточні завдання проекту
        current_tasks = set(self.object.tasks.values_list('id', flat=True))
        new_tasks = set(form.cleaned_data['tasks'].values_list('id', flat=True))

        # Видаляємо завдання, які були зняті з проекту
        tasks_to_remove = current_tasks - new_tasks
        for task_id in tasks_to_remove:
            task = get_object_or_404(Task, id=task_id)
            task.project = None  # Встановлюємо проект на None, щоб видалити його з проекту
            task.save()

        # Зберігаємо нові дані форми
        return super().form_valid(form)
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['tasks'] = Task.objects.filter(project=self.object)  # Отримуємо всі завдання для цього проекту
        return context
    
class ProjectDeleteView(LoginRequiredMixin, DeleteView):
    model = Project
    template_name = 'tasks/delete_project.html'  # Шаблон для підтвердження видалення проекту

    def get_object(self, queryset=None):
        # Отримуємо проект за ID
        return get_object_or_404(Project, id=self.kwargs['pk'])

    def get_success_url(self):
        # Перенаправляємо на список проектів після успішного видалення
        return reverse_lazy('projects-list')  # Змініть на вашу URL для списку проектів