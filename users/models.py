from django.contrib.auth.models import User
from django.db import models
from django.utils.timezone import now

# ==========================
# Tenant Model
# ==========================

class Tenant(models.Model):
    
    """Represents a business entity (organization).
    Fields:
    - name (CharField): The name of the tenant (e.g., company name).
    - domain (CharField): A unique domain identifier for the tenant.
    - owner (OneToOneField): The user who owns this tenant (must be unique).
    - logo (ImageField): Optional logo image for branding purposes.

    Example:
    Tenant(name='Acme Corp', domain='acme.yourapp.com')"""
    
    name = models.CharField(max_length=255)
    domain = models.CharField(max_length=255, unique=True)
    owner = models.OneToOneField(User, on_delete=models.CASCADE, related_name="tenant")
    logo = models.ImageField(upload_to="tenant_logos/", null=True, blank=True)  # ✅ Add logo field

    def __str__(self):
        return self.name

# ==========================
# UserProfile Model
# ==========================

class UserProfile(models.Model):
    """Extends the default User model to include roles and tenants.
    Fields:
    - user (OneToOneField): Reference to the built-in User model.
    - tenant (ForeignKey): The tenant to which the user belongs.
    - role (CharField): The role of the user within the tenant (admin, manager, etc.).

    Constraints:
    - unique_together: Ensures each user is unique within a tenant.

    Example:
    UserProfile(user=<User: john>, tenant=<Tenant: Acme>, role='manager')"""
    
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE)

    ROLE_CHOICES = [
        ('admin', 'Admin'),
        ('manager', 'Manager'),
        ('accountant', 'Accountant'),
        ('user', 'User'),
    ]
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='user')

    class Meta:
        unique_together = ('user', 'tenant')

    def __str__(self):
        return f'{self.user.username} ({self.role})'

# ==========================
# Client Model
# ==========================

class Client(models.Model):
    
    """Represents a business client who receives invoices.
    Represents a client who is associated with a tenant and receives invoices.

    Fields:
    - tenant (ForeignKey): The tenant who owns this client.
    - name (CharField): The full name of the client.
    - email (EmailField): The client’s email address (must be unique).
    - phone (CharField): Client’s contact number.
    - address (CharField): Client’s address.
    - details (CharField): Optional additional information.

    Example:
    Client(name="John Doe", email="john@example.com", phone="1234567890")"""
    
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE)
    name = models.CharField(max_length=255)
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=20)
    address = models.CharField(max_length=100, default='N/A')
    details = models.CharField(max_length=128, default='N/A')

    def __str__(self):
        return self.name
