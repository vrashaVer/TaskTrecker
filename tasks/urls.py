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
    path('tasks/delete/<int:pk>/', views.TaskDeleteView.as_view(), name='task_delete'),
    path('create/', views.TaskCreateView.as_view(), name='create-task'),
    path('login/', views.CustomLoginView.as_view(), name='login'),
    path('logout/', LogoutView.as_view(), name='logout'), 
]


if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)