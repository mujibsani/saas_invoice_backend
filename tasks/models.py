from django.db import models
from django.apps import apps

def get_user_profile():
    return apps.get_model('users', 'UserProfile')

def get_tenant():
    return apps.get_model('users', 'Tenant')

class Task(models.Model):
    STATUS_CHOICES = [
        ('to_do', 'To-Do'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('blocked', 'Blocked'),
    ]
    PRIORITY_CHOICES = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('urgent', 'Urgent'),
    ]
    tenant = models.ForeignKey('users.Tenant', on_delete=models.CASCADE)
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    assignee = models.ForeignKey('users.UserProfile', on_delete=models.SET_NULL, null=True, related_name='tasks')
    created_by = models.ForeignKey('users.UserProfile', on_delete=models.CASCADE, related_name='created_tasks')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default='medium')
    due_date = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return self.title

class SubTask(models.Model):
    task = models.ForeignKey(Task, on_delete=models.CASCADE, related_name='subtasks')
    title = models.CharField(max_length=255)
    status = models.CharField(max_length=20, choices=Task.STATUS_CHOICES, default='pending')
    
    def __str__(self):
        return self.title

class TaskDependency(models.Model):
    task = models.ForeignKey(Task, on_delete=models.CASCADE, related_name='dependencies')
    depends_on = models.ForeignKey(Task, on_delete=models.CASCADE, related_name='dependent_tasks')
    
    def __str__(self):
        return f"{self.task.title} depends on {self.depends_on.title}"
