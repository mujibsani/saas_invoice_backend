from django.contrib import admin
from django.contrib.auth.models import User
from django.contrib.auth.admin import UserAdmin as DefaultUserAdmin
from .models import  Client, Tenant, UserProfile

# ========================
# Custom User Admin
# ========================

"""Unregister the default User admin to customize it."""
admin.site.unregister(User)

@admin.register(User)
class CustomUserAdmin(DefaultUserAdmin):

    """Custom admin configuration for Django's built-in User model.

    - Enhances the user listing with additional fields.
    - Adds filters for user status and creation date.
    - Displays read-only fields like last login and date joined."""

    list_display = ("username", "email", "is_active", "date_joined")
    search_fields = ("username", "email")
    list_filter = ("is_active", "date_joined")
    readonly_fields = ("date_joined", "last_login")


# ========================
# Tenant Admin
# ========================
@admin.register(Tenant)
class TenantAdmin(admin.ModelAdmin):
    """
    Admin interface customization for the Tenant model.

    - Displays key tenant details like name, domain, and owner.
    - Includes a method to show logo status or path.
    - Provides search by name and domain.
    """
    list_display = ("name", "domain", "owner", "get_logo")
    search_fields = ("name", "domain")

    @admin.display(description="Logo")
    def get_logo(self, obj):
        """
        Admin method to show tenant logo URL or fallback text.

        Returns:
            str: Logo URL if present, otherwise 'No Logo'.
        """
        return obj.logo.url if obj.logo else "No Logo"

# ========================
# Client Admin
# ========================
@admin.register(Client)
class ClientAdmin(admin.ModelAdmin):
    """
    Admin panel configuration for the Client model.

    - Shows key fields such as name, email, and phone in the list view.
    - Supports searching clients by name and email.
    """
    list_display = ("name", "email", "phone")
    search_fields = ("name", "email")

# ========================
# UserProfile Admin
# ========================
@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    """
    Admin configuration for UserProfile model.

    - Displays user, role, and tenant in the list view.
    - Allows filtering by role and tenant.
    """
    list_display = ("user", "role", "tenant")
    list_filter = ("role", "tenant")


# ========================
# Customize Django Admin Panel Titles
# ========================

"""Change the Django admin panel branding for a better user experience"""

admin.site.site_header = "Invoice & Expense Management Admin"
admin.site.site_title = "Business Finance System"
admin.site.index_title = "Welcome to the Management Dashboard"

