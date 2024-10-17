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
    path('register/', views.RegisterView.as_view(), name='register'),
    path('projects/',views.ProjectListView.as_view(), name='projects-list'),
    path('projects/<int:project_id>/tasks/create/', views.TaskCreateView.as_view(), name='task_create_from_project'),
    path('projects/<int:pk>/', views.ProjectDetailView.as_view(), name='project_detail'),
    path('projects/create/', views.ProjectCreateView.as_view(), name='project_create'),
    path('projects/<int:pk>/edit/', views.ProjectUpdateView.as_view(), name='project_edit'),
    path('projects/<int:pk>/delete/', views.ProjectDeleteView.as_view(), name='project_delete'),
    path('task/<int:pk>/upload_file/', views.UploadFileView.as_view(), name='upload_file'),
    path('tasks/delete_file/<int:file_id>/', views.DeleteFileView.as_view(), name='delete_file'),
    path('tasks/<int:task_id>/add_comment/', views.AddCommentView.as_view(), name='add_comment'),
    path('tasks/<int:task_id>/complete/', views.MarkTaskCompletedView.as_view(), name='task_complete'),
    path('profile/', views.UserProfileView.as_view(), name='user_profile'),
    path('friends/', views.FriendsView.as_view(), name='friends'),
    path('friends/remove/<str:username>/', views.FriendsView.as_view(), name='remove_friend'),  
    path('friends/accept/<int:request_id>/', views.FriendsView.as_view(), name='accept_friend_request'),  
    path('profile/<str:username>/', views.FriendProfileView.as_view(), name='friend_profile'),
    path('remove_friend/<str:username>/',views.RemoveFriendView.as_view(), name='remove_friend'),
]


if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

