from django.db import models
from django.contrib.auth.models import User
from django.conf import settings

class Task(models.Model):
    PRIORITY_CHOICES = [
        ('L', 'Low'),
        ('M', 'Medium'),
        ('H', 'High'),
    ]

    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('IN_PROGRESS', 'In Progress'),
        ('COMPLETED', 'Completed'),
    ]

    name = models.CharField(max_length=100)
    description = models.TextField()
    deadline = models.DateField(null=True, blank=True)
    priority = models.CharField(max_length=1, choices=PRIORITY_CHOICES, default='M')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    owner = models.ForeignKey(User, on_delete=models.CASCADE)
    project = models.ForeignKey('Project', on_delete=models.SET_NULL, null=True, blank=True,related_name='tasks')
    image = models.ImageField(upload_to='task_images/', null=True, blank=True)

    def __str__(self):
        return self.name
    

class Project(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField()
    deadline = models.DateField(null=True, blank=True)
    participants = models.ManyToManyField(User, related_name='projects')
    owner = models.ForeignKey(User, on_delete=models.CASCADE)

    def __str__(self):
        return self.name
    
    def get_tasks(self):
        return self.tasks.all()
    
class Comment(models.Model):
    task = models.ForeignKey(Task, on_delete=models.CASCADE, related_name='comments')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    text = models.TextField()
    created_date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'Comment by {self.user.username} on {self.task.name}'
    


class TaskFile(models.Model):
    task = models.ForeignKey(Task, on_delete=models.CASCADE, related_name='task_files')
    file = models.FileField(upload_to='task_files/')

    def __str__(self):
        return self.file.name

    class Meta:
        unique_together = ('task', 'file')
  
class ProfilePhoto(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    photo = models.ImageField(upload_to='profile_photos/', blank=True, null=True) 

    def __str__(self):
        return f"{self.user.username}'s Profile Photo"

class Friend(models.Model):
    user = models.ForeignKey(User, related_name='friends', on_delete=models.CASCADE)
    friend = models.ForeignKey(User, related_name='friend_of', on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'friend')  # Зробити дружбу унікальною для кожної пари

    def __str__(self):
        return f"{self.user.username} is friends with {self.friend.username}"
    

class FriendRequest(models.Model):
    from_user = models.ForeignKey(User, related_name='friend_requests_sent', on_delete=models.CASCADE)
    to_user = models.ForeignKey(User, related_name='friend_requests_received', on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    accepted = models.BooleanField(default=False)  # Статус запиту

    def __str__(self):
        return f"{self.from_user.username} -> {self.to_user.username} ({'Accepted' if self.accepted else 'Pending'})"
    
