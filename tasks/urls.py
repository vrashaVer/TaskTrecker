from django.urls import path
from tasks import views
from django.contrib.auth.views import LogoutView
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('', views.HomePageView.as_view(), name='home'),
    path('tasks/', views.TaskListView.as_view(), name='tasks-list'),
    path('task/<int:pk>/', views.TaskDetailView.as_view(), name='task_detail'),
    path('tasks/edit/<int:pk>/', views.TaskEditView.as_view(), name='task_edit'), 
    path('task/<int:pk>/delete/', views.TaskDeleteView.as_view(), name='task_delete'),
    path('tasks/create/', views.TaskCreateView.as_view(), name='create-task'),
    path('login/', views.CustomLoginView.as_view(), name='login'),
    path('logout/', LogoutView.as_view(), name='logout'), 
    path('projects/',views.ProjectListView.as_view(), name='projects-list'),
    path('projects/<int:project_id>/tasks/create/', views.TaskCreateView.as_view(), name='task_create_from_project'),
    path('projects/<int:pk>/', views.ProjectDetailView.as_view(), name='project_detail'),
    path('projects/create/', views.ProjectCreateView.as_view(), name='project_create'),
    path('projects/<int:pk>/edit/', views.ProjectUpdateView.as_view(), name='project_edit'),
    path('projects/<int:pk>/delete/', views.ProjectDeleteView.as_view(), name='project_delete'),

]


if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

