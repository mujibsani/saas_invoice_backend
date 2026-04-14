from django.contrib import admin
from .models import Task

@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = ('title', 'assigned_to', 'status', 'created_at', 'updated_at')
    list_filter = ('status', 'assigned_to')
    search_fields = ('title', 'assigned_to__username')