from rest_framework import generics
from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import PermissionDenied
from .models import Task
from .serializers import TaskSerializer
from .permissions import IsAdminUser

class TaskListCreateView(generics.ListCreateAPIView):
    serializer_class = TaskSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
        if user.userprofile.role == 'admin':
            return Task.objects.filter(assigned_to__userprofile__tenant=user.userprofile.tenant)  # Admin sees all tenant tasks
        return Task.objects.filter(assigned_to=user)  # Regular users see only their tasks
    
    def perform_create(self, serializer):
        """Admin assigns a task to a user within the same tenant."""
        if self.request.user.userprofile.role != 'admin':
            raise PermissionDenied("Only admins can assign tasks.")
        serializer.save()

class TaskDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = TaskSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
        if user.userprofile.role == 'admin':
            return Task.objects.filter(assigned_to__userprofile__tenant=user.userprofile.tenant)  # Admin sees all tasks in the tenant
        return Task.objects.filter(assigned_to=user)  # Regular users see only their tasks