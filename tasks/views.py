from django.views.generic import TemplateView
from django.views.generic import ListView, DetailView, UpdateView, DeleteView, CreateView
from django.shortcuts import render, get_object_or_404
from django.urls import reverse_lazy, reverse
from .models import Task
from datetime import datetime, timedelta
from .forms import TaskForm
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.views import LoginView, LogoutView

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

class TaskEditView(UpdateView):
    model = Task
    form_class = TaskForm
    template_name = 'tasks/task_edit.html'  

    def get_success_url(self):
        return reverse_lazy('tasks-list')

class TaskDeleteView(DeleteView):
    model = Task
    success_url = reverse_lazy('tasks-list')

class TaskCreateView(LoginRequiredMixin, CreateView):
    model = Task
    form_class = TaskForm
    template_name = 'tasks/create_task.html'
    success_url = reverse_lazy('tasks-list')  

    def form_valid(self, form):
        form.instance.owner = self.request.user  
        return super().form_valid(form)
    

class CustomLoginView(LoginView):
    template_name = 'tasks/registration/login.html'  # Шаблон для авторизації
    success_url = reverse_lazy('tasks-list')

