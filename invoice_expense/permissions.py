from rest_framework.permissions import BasePermission

class IsAdminUser(BasePermission):
    """
    Custom permission to allow only admins to perform certain actions.
    """
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.userprofile.role == 'admin'

class CanCreateInvoice(BasePermission):
    """
    Allow regular users to create invoices but prevent them from updating or deleting.
    """
    def has_permission(self, request, view):
        if request.method == "POST":
            return request.user.is_authenticated  # Allow all authenticated users to create
        return request.user.userprofile.role == "admin"  # Only admins can update or delete

class CanViewInvoices(BasePermission):
    """
    Allow users to view only their assigned invoices or if they are admin.
    """
    def has_permission(self, request, view):
        return request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        return obj.assigned_users.filter(id=request.user.id).exists() or request.user.userprofile.role == "admin"
