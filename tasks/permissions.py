from rest_framework.permissions import BasePermission

class IsAdminUser(BasePermission):
    """
    Custom permission to allow only admins to perform certain actions.
    """
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.userprofile.role == 'admin'

class CanUpdateTask(BasePermission):
    """
    Allows users to update only their assigned tasks.
    """
    def has_object_permission(self, request, view, obj):
        return request.user in obj.assigned_to.all() or request.user == obj.created_by
