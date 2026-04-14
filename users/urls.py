from django.urls import path
from .views import (
    RegisterView, LoginView, AddUserView, UserListView, 
    ClientListCreateView, ClientDetailView, 
    UserProfileView, DeleteUserView,
    ToggleUserStatusView, ResetUserPasswordView, 
    CheckTenantView, CheckUsernameView, CheckEmailView, 
    TenantInfoView, TenantLogoUploadView, TenantUpdateView, 
)

urlpatterns = [
    # ==========================
    # User Authentication
    # ==========================
    path('register/', RegisterView.as_view(), name='register'),  # Register Admin (Creates Tenant)
    path('login/', LoginView.as_view(), name='login'),  # Login User (Returns JWT Token)
    path('add-user/', AddUserView.as_view(), name='add-user'),  # Admin Adds New Users
    path('user-list/', UserListView.as_view(), name='user-list'),  # Get List of Users Under Tenant
    path('profile/', UserProfileView.as_view(), name='user-profile'),  # ✅ User Profile API
    path('delete-user/<int:user_id>/', DeleteUserView.as_view(), name='delete-user'),  # ✅ Delete User
    path('toggle-user-status/<int:user_id>/', ToggleUserStatusView.as_view(), name='toggle-user-status'),
    path('reset-password/<int:user_id>/', ResetUserPasswordView.as_view(), name='reset-password'),

    # ==========================
    # Tenant Information
    # ==========================
    path("tenant-info/", TenantInfoView.as_view(), name="tenant-info"),  # Get Current Tenant Info
    path("tenant/upload-logo/", TenantLogoUploadView.as_view(), name="upload-tenant-logo"),
    path("tenant/update/", TenantUpdateView.as_view(), name="tenant-update"),
    # ==========================
    # Client Management
    # ==========================
    path('clients/', ClientListCreateView.as_view(), name='client-list'),  # List & Create Clients
    path('clients/<int:pk>/', ClientDetailView.as_view(), name='client-detail'),  # View, Update & Delete Client

    
    # ==========================
    # Live Check username and email
    # ==========================
    path("check-username/", CheckUsernameView.as_view(), name="check-username"),
    path("check-email/", CheckEmailView.as_view(), name="check-email"),
    path("check-tenant/", CheckTenantView.as_view(), name="check-tenant"),
    
    
]