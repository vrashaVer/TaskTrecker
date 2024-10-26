from django.views.generic import TemplateView
from django.views.generic import ListView, DetailView, UpdateView, DeleteView, CreateView
from django.shortcuts import render, get_object_or_404,redirect
from django.urls import reverse_lazy, reverse
from .models import Task, Project, TaskFile, Comment, ProfilePhoto,Friend,FriendRequest
from datetime import datetime, timedelta
from .forms import TaskForm, ProjectForm, CommentForm, CustomUserCreationForm,ProfilePhotoForm
from django.contrib.auth import login
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.views import LoginView
from django.db.models import Q
from django import forms
from django.views import View
from django.http import HttpResponseRedirect
from django.http import JsonResponse
from tasks.mixins import UserIsOwner, ProjectOwnerOrParticipantMixin
from django.core.exceptions import PermissionDenied
from django.contrib import messages
from django.contrib.auth.models import User
from django.utils import timezone


class HomePageView(TemplateView):
    template_name = 'tasks/home.html'



class TaskListView(ListView):
    model = Task
    template_name = 'tasks/tasks_list.html'
    context_object_name = 'tasks'
    
    def get_queryset(self):
        if self.request.user.is_authenticated:
            queryset = Task.objects.filter(
                Q(owner=self.request.user) | Q(project__participants=self.request.user)
            )

            query = self.request.GET.get('search')
            if query:
                queryset = queryset.filter(name__icontains=query)

            # Фільтрація за строком здачі
            deadline = self.request.GET.get('deadline')
            if deadline:
                try:
                    deadline_date = datetime.strptime(deadline, "%Y-%m-%d").date()
                    queryset = queryset.filter(deadline=deadline_date)
                except ValueError:
                    # Обробка випадку, якщо строку дати неможливо конвертувати
                    queryset = queryset.none()

            # Фільтрація за статусом
            status = self.request.GET.get('status')
            if status:
                queryset = queryset.filter(status=status.upper())

            
            # Фільтрація за пріоритетом
            priority = self.request.GET.get('priority')
            if priority:
                queryset = queryset.filter(priority=priority)

            sort_order = self.request.GET.get('sort')
            if sort_order == 'asc':
                queryset = queryset.order_by('deadline', 'id')  # Сортування по зростанню терміна
            elif sort_order == 'desc':
                queryset = queryset.order_by('-deadline', 'id')  # Сортування по спаданню терміна
            
            # Додайте завдання без терміна в кінець
            queryset = queryset.order_by('-deadline') | queryset.filter(deadline__isnull=True)


            
        else:
            queryset = Task.objects.none()
       
        
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.request.user.is_authenticated:
            upcoming_deadline = datetime.now() + timedelta(days=3)
            current_time = timezone.now()
            context['urgent_tasks'] = Task.objects.filter(owner=self.request.user,
                                                        deadline__gte=current_time,
                                                        deadline__lte=upcoming_deadline
                                                        ).exclude(status='COMPLETED').order_by('deadline')
            
        else:
            context['urgent_tasks'] = Task.objects.none()
            

        return context

  


class TaskDetailView(LoginRequiredMixin,DetailView):
    model = Task
    template_name = 'tasks/task_detail.html'
    context_object_name = 'task'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['next'] = self.request.GET.get('next')  # Додаємо параметр next в контекст
        context['task_files'] = TaskFile.objects.filter(task=self.object) 
        context['comments'] = Comment.objects.filter(task=self.object).order_by('created_date')
        context['comment_form'] = CommentForm()
        return context
    

class TaskEditView(LoginRequiredMixin,UpdateView):
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

        uploaded_files = self.request.FILES.getlist('new_files')
        for file in uploaded_files:
            TaskFile.objects.create(task=self.object, file=file)

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
        context['task_files'] = TaskFile.objects.filter(task=self.object)
        return context
    def post(self, request, *args, **kwargs):
        print("Received POST request")  # Логування
        return super().post(request, *args, **kwargs)

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
        task = form.save()

        files = self.request.FILES.getlist('files')  # Отримуємо список файлів
        for f in files:
            task_file = TaskFile(task=task, file=f)
            task_file.save()

        
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

            sort_order = self.request.GET.get('sort')
            if sort_order == 'asc':
                queryset = queryset.order_by('deadline', 'id')  # Сортування по зростанню терміна
            elif sort_order == 'desc':
                queryset = queryset.order_by('-deadline', 'id')
        else:
            queryset = Project.objects.none()
       
        
        return queryset.distinct()
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.request.user.is_authenticated:
            upcoming_deadline = datetime.now() + timedelta(days=3)
            current_time = timezone.now()
            context['upcoming_projects'] = Project.objects.filter(
                                                        Q(owner=self.request.user) | Q(participants=self.request.user),
                                                        deadline__gte=current_time,  
                                                        deadline__lte=upcoming_deadline
                                                    ).order_by('deadline')
        else:
            context['upcoming_projects'] = Project.objects.none()

        
        return context
    

class ProjectCreateView(LoginRequiredMixin,CreateView):
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
    

class ProjectDetailView(LoginRequiredMixin,DetailView):
    model = Project
    template_name = 'tasks/project_detail.html'
    context_object_name = 'project'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        project = self.get_object()  # Отримуємо поточний проєкт
        context['tasks'] = project.tasks.all()  # Додаємо в контекст завдання, прив'язані до проєкту
        context['user'] = self.request.user

        context['next_url'] = self.request.GET.get('next', reverse_lazy('projects-list'))
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

        tasks_to_add = new_tasks - current_tasks
        for task_id in tasks_to_add:
            task = get_object_or_404(Task, id=task_id)
            task.project = self.object  # Додаємо завдання до проекту
            task.save()

        # Зберігаємо нові дані форми
        return super().form_valid(form)
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['tasks'] = Task.objects.filter(project=self.object)  # Отримуємо всі завдання для цього проекту
        return context
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['owner'] = self.request.user  # Передаємо власника до форми
        return kwargs
    
class ProjectDeleteView(LoginRequiredMixin, DeleteView):

    def get_object(self, queryset=None):
        # Отримуємо проект за ID
        return get_object_or_404(Project, id=self.kwargs['pk'])

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        self.object.delete()  # Виконуємо видалення
        next_url = request.POST.get('next', reverse_lazy('projects-list'))  # Отримуємо next параметр або повертаємо на список проектів
        return redirect(next_url)

    def get_success_url(self):
        return reverse_lazy('projects-list')
    



class DeleteFileView(LoginRequiredMixin,View):
    def post(self, request, file_id):
        file = get_object_or_404(TaskFile, id=file_id)
        task_id = file.task.id  # Зберігаємо ID завдання для перенаправлення
        file.delete()  # Видаляємо файл
        return redirect('task_detail', pk=task_id)

class UploadFileView(LoginRequiredMixin,View):
    def post(self, request, pk):
        task = get_object_or_404(Task, pk=pk)
        files = request.FILES.getlist('new_files')
        for file in files:
            TaskFile.objects.create(task=task, file=file)
        return redirect('task_detail', pk=task.pk)
    




class AddCommentView(LoginRequiredMixin,View):
    def post(self, request, task_id):
        text = request.POST.get('text')
        task = Task.objects.get(id=task_id)
        comment = Comment.objects.create(task=task, user=request.user, text=text)

        # Повертаємо дані коментаря у JSON-форматі
        return JsonResponse({
            'success': True,
            'username': comment.user.username,
            'created_date': comment.created_date.strftime("%d %b %Y %H:%M"),
            'text': comment.text
        })
    
class MarkTaskCompletedView(LoginRequiredMixin,View):
    def post(self, request, task_id):
        task = get_object_or_404(Task, id=task_id)

        # Змінюємо статус завдання
        task.status = 'COMPLETED'
        task.save()

         # Отримуємо URL, на який потрібно перенаправити користувача
        next_url = request.POST.get('next', 'tasks-list')  # Якщо немає 'next', то йдемо на tasks-list

        # Перенаправляємо користувача назад на сторінку
        return redirect(next_url)
    


class RegisterView(CreateView):
    form_class = CustomUserCreationForm
    template_name = 'tasks/registration/register.html'
    success_url = reverse_lazy('home')  # Замість 'home' вставте вашу цільову URL-адресу

    def form_valid(self, form):
        user = form.save()
        login(self.request, user)  # Автоматично увійти після реєстрації
        return redirect(self.success_url)
    
class CustomLoginView(LoginView):
    template_name = 'tasks/registration/login.html'  # Вкажіть свій шаблон для входу
    success_url = reverse_lazy('home')  # URL для перенаправлення після успішного входу


    
class UserProfileView(LoginRequiredMixin, View):
    template_name = 'tasks/user_profile.html'

    def get(self, request):
        # Отримання профільної фотографії, якщо вона існує
        profile_photo = ProfilePhoto.objects.filter(user=request.user).first()

        context = {
            'profile_photo': profile_photo,
            'user': request.user, 
            'form': ProfilePhotoForm(), # Додаємо користувача в контекст
        }
        return render(request, self.template_name, context)
    
    def post(self, request):
        # Обробка POST-запиту для завантаження фотографії
        profile_photo, created = ProfilePhoto.objects.get_or_create(user=request.user)

        form = ProfilePhotoForm(request.POST, request.FILES, instance=profile_photo)
        if form.is_valid():
            form.save()
            return redirect('user_profile')  # Змініть на правильне ім'я URL

        context = {
            'profile_photo': profile_photo,
            'user': request.user,
            'form': form,
        }
        return render(request, self.template_name, context)
        



class FriendsView(View):
    def get(self, request):
        # Пошук друзів
        search_query = request.GET.get('search', '')
        if search_query:
            users = User.objects.filter(username__icontains=search_query).exclude(id=request.user.id)
        else:
            users = User.objects.exclude(id=request.user.id)

        # Отримання списку друзів
        friends = Friend.objects.filter(user=request.user).values_list('friend', flat=True)
        friend_requests = FriendRequest.objects.filter(to_user=request.user, accepted=False)

        return render(request, 'tasks/friends.html', {
            'friends': User.objects.filter(id__in=friends),
            'friend_requests': friend_requests,
            'users': users,
            'search_query': search_query,
        })

    def post(self, request):
        action = request.POST.get('action')  # Отримати тип дії з POST-запиту

        if action == 'send_friend_request':
            friend_username = request.POST.get('friend_username')
            if friend_username == request.user.username:
                messages.warning(request, 'Ви не можете надіслати запит на дружбу самому собі.')
                return redirect('friends')
            try:
                friend = User.objects.get(username=friend_username)
            except User.DoesNotExist:
                messages.error(request, 'Користувач з таким ім\'ям не існує.')
                return redirect('friends')

            # Перевірка, чи вже є дружба
            if Friend.objects.filter(user=request.user, friend=friend).exists():
                messages.warning(request, 'Ви вже дружите з цим користувачем.')
            elif FriendRequest.objects.filter(from_user=request.user, to_user=friend).exists():
                messages.warning(request, 'Ви вже надіслали запит цьому користувачу.')
            else:
                FriendRequest.objects.create(from_user=request.user, to_user=friend)
                messages.success(request, f'Запит на дружбу надіслано {friend.username}.')

        elif action == 'accept_friend_request':
            request_id = request.POST.get('request_id')
            friend_request = get_object_or_404(FriendRequest, id=request_id, to_user=request.user)
            Friend.objects.create(user=request.user, friend=friend_request.from_user)
            Friend.objects.create(user=friend_request.from_user, friend=request.user)
            friend_request.delete()
            messages.success(request, f'Тепер ви друзі з {friend_request.from_user.username}.')

        elif action == 'reject_friend_request':
            request_id = request.POST.get('request_id')
            friend_request = get_object_or_404(FriendRequest, id=request_id, to_user=request.user)
            friend_request.delete()  # Видалити запит
            messages.info(request, 'Запит на дружбу відхилено.')

        elif action == 'remove_friend':
            friend_username = request.POST.get('friend_username')
            friend = get_object_or_404(User, username=friend_username)
            Friend.objects.filter(user=request.user, friend=friend).delete()
            messages.success(request, f'Ви видалили {friend.username} зі своїх друзів.')

        return redirect('friends')
    

class FriendProfileView(View):
    def get(self, request, username):
        friend = get_object_or_404(User, username=username)

        is_friend = Friend.objects.filter(user=request.user, friend=friend).exists()

        # Отримання запиту на дружбу (якщо є)
        friend_request = FriendRequest.objects.filter(from_user=friend, to_user=request.user, accepted=False).first()

        shared_projects = Project.objects.filter(
            (Q(owner=request.user) & Q(participants=friend)) |
            (Q(owner=friend) & Q(participants=request.user)) |
            (Q(participants=request.user) & Q(participants=friend))
        ).distinct()

        return render(request, 'tasks/friend_profile.html', {
            'friend': friend,
            'is_friend': is_friend,
            'friend_request': friend_request,
            'shared_projects': shared_projects,
        })
        
    
class RemoveFriendView(LoginRequiredMixin, View):
    def post(self, request, username):
        friend = get_object_or_404(User, username=username)

        # Видаляємо дружбу
        Friend.objects.filter(user=request.user, friend=friend).delete()
        Friend.objects.filter(user=friend, friend=request.user).delete()

        messages.success(request, f'Ви видалили {friend.username} зі своїх друзів.')
        return redirect('friends')  