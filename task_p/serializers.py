from rest_framework import serializers
from django.apps import apps

Task = apps.get_model('tasks', 'Task')
Subtask = apps.get_model('tasks', 'Subtask')
TaskComment = apps.get_model('tasks', 'TaskComment')
TaskAttachment = apps.get_model('tasks', 'TaskAttachment')
Notification = apps.get_model('tasks', 'Notification')
UserProfile = apps.get_model('users', 'UserProfile')

class TaskSerializer(serializers.ModelSerializer):
    created_by = serializers.ReadOnlyField(source='created_by.user.username')
    assigned_to = serializers.PrimaryKeyRelatedField(
        many=True, queryset=UserProfile.objects.all()
    )

    class Meta:
        model = Task
        fields = [
            'id', 'title', 'description', 'created_by', 'assigned_to',
            'status', 'priority', 'due_date', 'created_at', 'updated_at',
            'recurring'
        ]

class SubtaskSerializer(serializers.ModelSerializer):
    task = serializers.PrimaryKeyRelatedField(queryset=Task.objects.all())

    class Meta:
        model = Subtask
        fields = ['id', 'task', 'title', 'status']

class TaskCommentSerializer(serializers.ModelSerializer):
    task = serializers.PrimaryKeyRelatedField(queryset=Task.objects.all())
    user = serializers.ReadOnlyField(source='user.user.username')

    class Meta:
        model = TaskComment
        fields = ['id', 'task', 'user', 'comment', 'created_at']

class TaskAttachmentSerializer(serializers.ModelSerializer):
    task = serializers.PrimaryKeyRelatedField(queryset=Task.objects.all())

    class Meta:
        model = TaskAttachment
        fields = ['id', 'task', 'file', 'uploaded_at']

class NotificationSerializer(serializers.ModelSerializer):
    task_title = serializers.ReadOnlyField(source='task.title')

    class Meta:
        model = Notification
        fields = ['id', 'task', 'task_title', 'message', 'created_at', 'is_read']
