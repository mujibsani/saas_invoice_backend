from rest_framework import serializers
from rest_framework import serializers
from django.contrib.auth.models import User
from .models import UserProfile, Tenant, Client
from rest_framework import serializers

# ==========================
# User & Profile Serializers
# ==========================

class UserSerializer(serializers.ModelSerializer):
    """Serializer for User model (basic details only)."""
    """
    Serializer for the built-in Django User model.

    This serializer exposes basic user details such as:
    - id
    - username
    - email

    Typically used for read-only nested relationships within other serializers.
    """
    class Meta:
        model = User
        fields = ['id', 'username', 'email']

class UserProfileSerializer(serializers.ModelSerializer):
    """Serializer for UserProfile, including user and role."""
    """
    Serializer for the UserProfile model.

    - Includes nested user information via UserSerializer (read-only).
    - Exposes the user's role (e.g., 'admin', 'user').

    This serializer is commonly used when returning extended user data.
    """
    user = UserSerializer(read_only=True)  # Nested user details

    class Meta:
        model = UserProfile
        fields = ['user', 'role']

# ==========================
# Tenant Serializer
# ==========================

class TenantSerializer(serializers.ModelSerializer):
    
    """
    Serializer for the Tenant model.

    Fields:
    - id: Unique ID for the tenant.
    - name: The tenant's business or organization name.
    - domain: Subdomain or custom domain used by the tenant.
    - owner: ForeignKey to the user who created the tenant.
    - owner_username: Read-only field to expose the owner's username.
    - logo: Optional logo/image for the tenant.

    Notes:
    - `owner_username` is derived using a ReadOnlyField with source mapping.
    - `logo` is optional and supports file/image uploads.
    """
    owner_username = serializers.ReadOnlyField(source='owner.username')
    logo = serializers.ImageField(required=False)  # ✅ Include logo

    class Meta:
        model = Tenant
        fields = ['id', 'name', 'domain', 'owner', 'owner_username', 'logo']

# ==========================
# Client Serializer
# ==========================

class ClientSerializer(serializers.ModelSerializer):
    """
    Serializer for the Client model.

    Fields:
    - id: Client ID.
    - name: Full name of the client.
    - email: Email address.
    - phone: Phone number.
    - address: Physical address.
    - details: Additional notes or client-specific details.
    - tenant: ForeignKey to the tenant that owns this client.
    - tenant_name: Read-only field to show the tenant's name for context.

    Notes:
    - `tenant_name` is provided as a ReadOnlyField sourced from the related tenant.
    """
    tenant_name = serializers.ReadOnlyField(source='tenant.name')

    class Meta:
        model = Client
        fields = ['id', 'name', 'email', 'phone', 'address','details','tenant', 'tenant_name']