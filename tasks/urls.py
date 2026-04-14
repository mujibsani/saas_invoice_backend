from django.urls import path
from .views import TaskListCreateView, TaskUpdateStatusView, TaskDetailUpdateView

urlpatterns = [
    path('tasks/', TaskListCreateView.as_view(), name='task-list-create'),  # Admin: Create & List Tasks
    path('tasks/<int:pk>/', TaskDetailUpdateView.as_view(), name='task-details'),  # Admin: Create & List Tasks
    path('tasks/<int:pk>/update-status/', TaskUpdateStatusView.as_view(), name='task-update-status'),  # User: Update Task Status
]