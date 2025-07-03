from rest_framework import serializers
from django.apps import apps

Task = apps.get_model('tasks', 'Task')
SubTask = apps.get_model('tasks', 'SubTask')
TaskDependency = apps.get_model('tasks', 'TaskDependency')
UserProfile = apps.get_model('users', 'UserProfile')

class TaskSerializer(serializers.ModelSerializer):
    assignee = serializers.PrimaryKeyRelatedField(queryset=UserProfile.objects.all())
    created_by = serializers.ReadOnlyField(source='created_by.user.username')
    tenant = serializers.ReadOnlyField(source='tenant.id')
    priority = serializers.ChoiceField(choices=Task.PRIORITY_CHOICES, default='medium')

    class Meta:
        model = Task
        fields = ['id', 'tenant', 'title', 'description', 'assignee', 'created_by', 'status', 'priority', 'due_date', 'created_at', 'updated_at']
        read_only_fields = ['created_by', 'tenant']

class TaskStatusUpdateSerializer(serializers.ModelSerializer):
    """Serializer for users to update only task status."""
    class Meta:
        model = Task
        fields = ['status']

class SubTaskSerializer(serializers.ModelSerializer):
    class Meta:
        model = SubTask
        fields = ['id', 'task', 'title', 'status']

class TaskDependencySerializer(serializers.ModelSerializer):
    class Meta:
        model = TaskDependency
        fields = ['id', 'task', 'depends_on']
