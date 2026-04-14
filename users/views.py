from datetime import timedelta
from django.utils.timezone import now
from django.conf import settings
from django.db.models import Sum, F, Q
from django.contrib.auth.models import User
from django.contrib.auth import authenticate

from rest_framework import generics, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.parsers import MultiPartParser, FormParser

from users.models import Tenant, UserProfile,  Client,  UserProfile
from users.serializers import ( ClientSerializer, TenantSerializer)
from users.permissions import IsAdminUser

# ==========================
# Tanant Management Views
# ==========================
class TenantInfoView(APIView):
    """Retrieve Tenant Info including logo URL.

    GET /api/tenant/info/

    Returns the current tenant's basic information including:
    - ID
    - Name
    - Domain
    - Owner (id, username, email)
    - Logo URL

    Requires:
    - JWT authentication
    """
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user_profile = request.user.userprofile
        tenant = user_profile.tenant

        return Response({
            "id": tenant.id,
            "name": tenant.name,
            "domain": tenant.domain,
            "owner": {
                "id": tenant.owner.id,
                "username": tenant.owner.username,
                "email": tenant.owner.email,  # ✅ Include owner's email if needed
            },
            "logo": tenant.logo.url if tenant.logo else None  # ✅ Include logo URL
        })

class TenantUpdateView(APIView):
    """
    Update Tenant details.
    
    PUT /api/tenant/update/

    Updates the tenant details using partial update (PATCH behavior).
    Fields like name, domain, and logo can be updated.

    Requires:
    - JWT authentication
    """
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def put(self, request):
        tenant = request.user.userprofile.tenant  # Get the tenant linked to the user
        serializer = TenantSerializer(tenant, data=request.data, partial=True)

        if serializer.is_valid():
            serializer.save()
            return Response({"message": "Tenant updated successfully!", "data": serializer.data})
        
        return Response(serializer.errors, status=400)

class TenantLogoUploadView(APIView):
    """
    API View for Tenant Admins to upload a logo.
     POST /api/tenant/upload-logo/

    Uploads or updates the tenant's logo.
    Accepts multipart form data.

    Requires:
    - JWT authentication
    """
    parser_classes = (MultiPartParser, FormParser)
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request):
        tenant = request.user.tenant  # ✅ Get the tenant linked to the admin
        serializer = TenantSerializer(tenant, data=request.data, partial=True)

        if serializer.is_valid():
            serializer.save()
            return Response({"message": "Logo updated successfully!", "logo_url": serializer.data["logo"]})
        
        return Response(serializer.errors, status=400)

class RegisterView(APIView):
    """
    Creates a new admin user and tenant
    POST /api/auth/register/

    Creates a new tenant and its owner (admin user).
    - Creates a User (admin)
    - Creates a Tenant
    - Links the UserProfile to the tenant with admin role
    - Returns JWT token and tenant domain

    Public endpoint (no authentication required).
    """
    permission_classes = [AllowAny]

    def post(self, request):
        username = request.data.get('username')
        password = request.data.get('password')
        email = request.data.get('email')
        business_name = request.data.get('business_name')

        user = User.objects.create_user(username=username, password=password, email=email)
        tenant = Tenant.objects.create(name=business_name, domain=f'{username}.yourapp.com', owner=user)
        UserProfile.objects.create(user=user, tenant=tenant, role='admin')

        refresh = RefreshToken.for_user(user)

        return Response({
            'refresh': str(refresh),
            'access': str(refresh.access_token),
            'tenant_domain': tenant.domain,
            'message': 'Admin user registered successfully!'
        })

class LoginView(APIView):
    """
    Login API: Returns JWT token, user details, and role.
    POST /api/auth/login/

    Authenticates a user and returns:
    - Access & Refresh JWT tokens
    - User's username, role, and tenant name

    Public endpoint.
    """
    permission_classes = [AllowAny]

    def post(self, request):
        username = request.data.get("username")
        password = request.data.get("password")

        if not username or not password:
            return Response({"error": "Username and password are required."}, status=400)

        user = authenticate(username=username, password=password)

        if user is None:
            return Response({"error": "Invalid username or password."}, status=400)

        refresh = RefreshToken.for_user(user)
        user_profile = UserProfile.objects.get(user=user)

        return Response({
            "access": str(refresh.access_token),
            "refresh": str(refresh),
            "username": user.username,
            "role": user_profile.role,
            "tenant_name": user_profile.tenant.name,
            "message": "Login successful!"
        })

class AddUserView(APIView):
    """
    Only Admins Can Add Users
    POST /api/users/add/

    Allows an admin to add a new user under their tenant.

    Requires:
    - JWT authentication
    - Admin role
    """
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated, IsAdminUser]

    def post(self, request):
        username = request.data.get('username')
        password = request.data.get('password')
        email = request.data.get('email')
        role = request.data.get('role', 'viewer')  # Default role is 'viewer'

        tenant = request.user.userprofile.tenant
        new_user = User.objects.create_user(username=username, password=password, email=email)
        UserProfile.objects.create(user=new_user, tenant=tenant, role=role)

        return Response({'message': 'User added successfully!', 'username': username})


# ==========================
# Check for Tenant, username and email exist or not
# ==========================

class CheckTenantView(APIView):
    """
    heck if a tenant name already exists.
    GET /api/check/tenant/?tenant_name=

    Checks if the provided tenant name already exists.
    Public endpoint.
    """
    permission_classes = [AllowAny]

    def get(self, request):
        tenant_name = request.query_params.get("tenant_name")
        if not tenant_name:
            return Response({"error": "Tenant name is required"}, status=400)

        exists = Tenant.objects.filter(name=tenant_name).exists()
        return Response({"exists": exists})
    
class CheckUsernameView(APIView):
    """
    Check if a username already exists.
    GET /api/check/username/?username=

    Checks if a username is already taken.
    Public endpoint.
    """
    permission_classes = [AllowAny]

    def get(self, request):
        username = request.query_params.get("username")
        if not username:
            return Response({"error": "Username is required"}, status=400)

        exists = User.objects.filter(username=username).exists()
        return Response({"exists": exists})

class CheckEmailView(APIView):
    """
    Check if an email already exists.
    GET /api/check/email/?email=

    Checks if an email is already taken.
    Public endpoint.
    """
    permission_classes = [AllowAny]

    def get(self, request):
        email = request.query_params.get("email")
        if not email:
            return Response({"error": "Email is required"}, status=400)

        exists = User.objects.filter(email=email).exists()
        return Response({"exists": exists})


# ==========================
# User Management UserLogin)
# ==========================

class UserProfileView(APIView):
    """
    Returns the logged-in user's profile with role information.
    GET /api/user/profile/

    Returns details of the currently authenticated user:
    - Username
    - Email
    - Role
    - Tenant name

    Requires:
    - JWT authentication
    """
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user_profile = request.user.userprofile
        return Response({
            "username": request.user.username,
            "email": request.user.email,
            "role": user_profile.role,
            "tenant": user_profile.tenant.name
        })
        
        
# ==========================
# User Management (Only Admins Can Create Users)
# ==========================

class UserListView(APIView):
    """
    Fetch all users under the admin's tenant
    GET /api/users/

    Fetches all users under the same tenant as the admin.
    Only accessible by admin users.

    Requires:
    - JWT authentication
    - Admin role
    """
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        # ✅ Only admins can view users
        if request.user.userprofile.role != 'admin':
            return Response({'error': 'Only admins can view users.'}, status=403)

        tenant = request.user.userprofile.tenant  # Get the tenant of the logged-in admin
        users = UserProfile.objects.filter(tenant=tenant).select_related("user")  # Fetch users of the same tenant

        # ✅ Build correct response structure
        user_data = [
            {
                "id": user.user.id,
                "username": user.user.username,
                "email": user.user.email,
                "role": user.role,
                "is_active": user.user.is_active,  # ✅ Ensure `is_active` is returned correctly
                "tenant_id": tenant.id,  # ✅ Include Tenant ID
                "tenant_name": tenant.name  # ✅ Include Tenant Name
            }
            for user in users
        ]

        return Response(user_data, status=200)


class ToggleUserStatusView(APIView):
    """
    POST /api/users/<user_id>/toggle-status/

    Allows an admin to activate or deactivate a non-admin user.
    Prevents changes to admin status.

    Requires:
    - JWT authentication
    - Admin role
    """
    
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request, user_id):
        """Allow admin to activate or deactivate a user."""
        try:
            logged_in_user = request.user
            user_to_toggle = User.objects.get(id=user_id)

            # Only admins can activate/deactivate users
            if logged_in_user.userprofile.role != "admin":
                return Response({"error": "Only admins can activate/deactivate users."}, status=status.HTTP_403_FORBIDDEN)

            # Prevent modifying other admins
            if user_to_toggle.userprofile.role == "admin":
                return Response({"error": "Admin users cannot be deactivated!"}, status=status.HTTP_403_FORBIDDEN)

            # Toggle user status and save
            user_to_toggle.is_active = not user_to_toggle.is_active
            user_to_toggle.save()

            return Response({
                "message": f"User {'activated' if user_to_toggle.is_active else 'deactivated'} successfully.",
                "user": {
                    "id": user_to_toggle.id,
                    "username": user_to_toggle.username,
                    "email": user_to_toggle.email,
                    "role": user_to_toggle.userprofile.role,
                    "is_active": user_to_toggle.is_active
                }
            })

        except User.DoesNotExist:
            return Response({"error": "User not found."}, status=status.HTTP_404_NOT_FOUND)

class DeleteUserView(APIView):
    """Allow admin to Delete user."""
    """
    DELETE /api/users/<user_id>/

    Deletes a non-admin user from the system.
    Only accessible by admin users.

    Requires:
    - JWT authentication
    - Admin role
    """
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def delete(self, request, user_id):
        if request.user.userprofile.role != "admin":
            return Response({"error": "Only admins can delete users."}, status=status.HTTP_403_FORBIDDEN)

        try:
            user = User.objects.get(id=user_id)
            if user.userprofile.role == "admin":
                return Response({"error": "You cannot delete an admin."}, status=status.HTTP_403_FORBIDDEN)

            user.delete()
            return Response({"message": "User deleted successfully."}, status=status.HTTP_200_OK)
        except User.DoesNotExist:
            return Response({"error": "User not found."}, status=status.HTTP_404_NOT_FOUND)

class ResetUserPasswordView(APIView):
    """Allow admin to reset a user's password"""
    """
    POST /api/users/<user_id>/reset-password/

    Allows an admin to reset a user's password.
    Password must be at least 6 characters.

    Requires:
    - JWT authentication
    - Admin role
    """
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request, user_id):
        # ✅ Only admins can reset passwords
        if request.user.userprofile.role != 'admin':
            return Response({'error': 'Only admins can reset passwords.'}, status=403)

        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return Response({"error": "User not found."}, status=404)

        new_password = request.data.get("new_password")
        if not new_password or len(new_password) < 6:
            return Response({"error": "Password must be at least 6 characters long."}, status=400)

        user.set_password(new_password)
        user.save()

        return Response({"message": f"Password for {user.username} has been reset successfully."}, status=200)


# ==========================
# Client Management (Only Admins Can Create Clients)
# ==========================

class ClientListCreateView(generics.ListCreateAPIView):
    """Admin can create clients, and authenticated users can view them."""
    """
    Handles listing and creation of clients for the current tenant.

    - Authenticated users (Admin or User) can view the list of clients
      associated with their tenant.
    - Only users with the 'admin' role are allowed to create new clients.
    - On creation, the tenant is automatically assigned based on the
      authenticated user's profile.

    Methods:
        - GET: List all clients for the authenticated user's tenant.
        - POST: Create a new client (admin only).

    Permissions:
        - JWT authentication required.
        - Listing allowed for all authenticated users.
        - Creation restricted to admin users only.
    """
    authentication_classes = [JWTAuthentication]
    serializer_class = ClientSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Filter clients by the tenant of the logged-in user."""
        """
        Returns a queryset of clients filtered by the tenant associated
        with the currently authenticated user.

        Ensures that users can only access clients from their own tenant.
        """
        return Client.objects.filter(tenant=self.request.user.userprofile.tenant)

    def create(self, request, *args, **kwargs):
        """Override create method to enforce admin-only restriction."""
        """
        Creates a new client for the authenticated admin's tenant.

        - Validates user is an admin.
        - Automatically assigns the tenant to the new client instance.
        - Returns serialized client data on success or validation errors on failure.
        """
        if request.user.userprofile.role != 'admin':
            return Response({"error": "Only admins can create clients."}, status=status.HTTP_403_FORBIDDEN)

        # Automatically assign tenant before saving
        data = request.data.copy()  # Create a mutable copy
        data["tenant"] = request.user.userprofile.tenant.id  # Assign tenant ID

        serializer = self.get_serializer(data=data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class ClientDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    Handles retrieve, update, and delete operations for a single client.

    - Only admin users are permitted to update or delete clients.
    - All operations are scoped to the tenant of the authenticated user.

    Methods:
        - GET: Retrieve a specific client's details.
        - PUT/PATCH: Update a client's information (admin only).
        - DELETE: Delete a client record (admin only).

    Permissions:
        - JWT authentication required.
        - Admin privileges required for update and delete operations.
    """
    authentication_classes = [JWTAuthentication]
    serializer_class = ClientSerializer
    permission_classes = [IsAuthenticated, IsAdminUser]  # Only admins can update/delete clients

    def get_queryset(self):
        """
        Returns a queryset of clients filtered by the tenant of the
        currently authenticated user.

        Ensures tenant isolation across all retrieve/update/delete operations.
        """
        return Client.objects.filter(tenant=self.request.user.userprofile.tenant)
