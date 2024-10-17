from django.core.exceptions import PermissionDenied
from django.shortcuts import  get_object_or_404
from .models import Project,Task

class UserIsOwner(PermissionDenied):
    def dispatch(self,request, *args, **kwargs):
        instance = self.get_object()
        if instance.owner != self.request.user:
            raise PermissionDenied
        return super().dispatch(request, *args, **kwargs)
    
class ProjectOwnerOrParticipantMixin(PermissionDenied):
    def dispatch(self, request, *args, **kwargs):
        project = get_object_or_404(Project, pk=kwargs.get('pk'))  # Отримуємо проект за pk
        if not (project.owner == request.user or request.user in project.participants.all()):
            raise PermissionDenied()
        return super().dispatch(request, *args, **kwargs)