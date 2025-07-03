from rest_framework import generics, permissions
from rest_framework.response import Response
from rest_framework.views import APIView
from django.apps import apps
from rest_framework.permissions import IsAuthenticated
from .serializers import TaskSerializer, TaskStatusUpdateSerializer

Task = apps.get_model('tasks', 'Task')
UserProfile = apps.get_model('users', 'UserProfile')

class IsAdminUser(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.userprofile.role == 'admin'

class TaskListCreateView(generics.ListCreateAPIView):
    """Admin can create and view all tasks, users can only see assigned tasks."""
    permission_classes = [IsAuthenticated]
    serializer_class = TaskSerializer
    
    def get_queryset(self):
        user_profile = self.request.user.userprofile
        if user_profile.role == 'admin':
            return Task.objects.filter(tenant=user_profile.tenant)
        return Task.objects.filter(tenant=user_profile.tenant, assignee=user_profile)
    
    def perform_create(self, serializer):
        user_profile = self.request.user.userprofile
        if user_profile.role != 'admin':
            return Response({'error': 'Only admins can create tasks.'}, status=403)
        
        assignee = serializer.validated_data.get('assignee')
        if assignee and not UserProfile.objects.filter(id=assignee.id, tenant=user_profile.tenant).exists():
            return Response({'error': 'Assignee must belong to the same tenant.'}, status=400)
        
        serializer.save(created_by=user_profile, tenant=user_profile.tenant)

class TaskDetailUpdateView(generics.RetrieveUpdateAPIView):
    """Admin can retrieve and update any task. Users can only update status."""
    permission_classes = [IsAuthenticated]
    serializer_class = TaskSerializer

    def get_queryset(self):
        user_profile = self.request.user.userprofile
        return Task.objects.filter(tenant=user_profile.tenant)

    def patch(self, request, *args, **kwargs):
        user_profile = request.user.userprofile
        task = self.get_object()

        if user_profile.role != 'admin' and task.assignee != user_profile:
            return Response({'error': 'You can only update your assigned tasks.'}, status=403)

        return super().patch(request, *args, **kwargs)

class TaskUpdateStatusView(APIView):
    """Users can update only the status of their assigned tasks."""
    permission_classes = [IsAuthenticated]
    
    def patch(self, request, pk):
        user_profile = request.user.userprofile
        try:
            task = Task.objects.get(id=pk, tenant=user_profile.tenant)
        except Task.DoesNotExist:
            return Response({'error': 'Task not found.'}, status=404)
        
        if user_profile.role != 'admin' and task.assignee != user_profile:
            return Response({'error': 'You can only update your assigned tasks.'}, status=403)
        
        serializer = TaskStatusUpdateSerializer(task, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response({'message': 'Task status updated successfully.', 'data': serializer.data})
        return Response(serializer.errors, status=400)

class TaskDeleteView(generics.DestroyAPIView):
    """Only admins can delete tasks."""
    permission_classes = [IsAuthenticated, IsAdminUser]

    def get_queryset(self):
        user_profile = self.request.user.userprofile
        return Task.objects.filter(tenant=user_profile.tenant)
