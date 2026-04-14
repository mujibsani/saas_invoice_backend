from django.contrib.auth.models import User
from django.db import models
from django.utils.timezone import now
from django.conf import settings

# ==========================
# Invoice & InvoiceItem Models
# ==========================
class Invoice(models.Model):
    """
    Represents an invoice associated with a tenant and a client.

    Attributes:
        tenant (ForeignKey): Reference to the tenant owning this invoice.
        client (ForeignKey): Reference to the client billed by this invoice.
        assigned_users (ManyToManyField): Users assigned to this invoice.
        invoice_number (CharField): Unique identifier, auto-generated if blank.
        due_date (DateField): Date by which payment is due.
        status (CharField): Current status of the invoice ('pending', 'paid', 'overdue').
        created_at (DateTimeField): Timestamp when the invoice was created.

    Methods:
        save(): Overrides save to auto-generate invoice_number if missing.
        total_amount(): Calculates sum of all invoice item amounts.
        __str__(): Returns a string representation including invoice number and client name.
    """
    
    tenant = models.ForeignKey(settings.TENANT_MODEL, on_delete=models.CASCADE)
    client = models.ForeignKey(settings.CLIENT_MODEL, on_delete=models.CASCADE)
    assigned_users = models.ManyToManyField(User, blank=True)
    invoice_number = models.CharField(max_length=50, unique=True, blank=True)
    due_date = models.DateField()
    status = models.CharField(
        max_length=20, 
        choices=[("pending", "Pending"), ("paid", "Paid"), ("overdue", "Overdue")], 
        default="pending"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        """
        Auto-generates a unique invoice number if not provided.

        The format is: INV-{year}-{sequential_number}, 
        where sequential_number is zero-padded to 5 digits.
        """
        if not self.invoice_number:
            last_invoice = Invoice.objects.filter(tenant=self.tenant).order_by("-created_at").first()
            next_number = 1 if not last_invoice else int(last_invoice.invoice_number.split("-")[-1]) + 1
            self.invoice_number = f"INV-{now().year}-{next_number:05d}"  
        super().save(*args, **kwargs)

    def total_amount(self):
        """
        Calculate the total amount for the invoice.

        Returns:
            Decimal: Sum of (unit_price * quantity) for all invoice items.
        """
        return sum(item.unit_price * item.quantity for item in self.items.all())

    def __str__(self):
        """Return string representation showing invoice number and client."""
        return f"Invoice {self.invoice_number} - {self.client.name}"
    
class InvoiceItem(models.Model):
    """
    Represents an item or service billed in an invoice.

    Attributes:
        invoice (ForeignKey): The invoice this item belongs to.
        name (CharField): Item or service name.
        description (TextField): Optional description.
        quantity (PositiveIntegerField): Quantity of the item (default 1).
        unit_price (DecimalField): Price per unit of the item.

    Methods:
        __str__(): String showing item name and total cost (quantity x unit_price).
    """
    
    invoice = models.ForeignKey(Invoice, related_name="items", on_delete=models.CASCADE)
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    quantity = models.PositiveIntegerField(default=1)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"{self.name} - {self.quantity} x {self.unit_price}"

# ==========================
# Expense Model
# ==========================

class Expense(models.Model):
    """
    Represents a business expense record.

    Attributes:
        tenant (ForeignKey): Tenant associated with the expense.
        category (CharField): Expense category (e.g. Travel, Office Supplies).
        amount (DecimalField): Monetary value of the expense.
        description (TextField): Detailed explanation of the expense.
        date (DateField): Date when the expense occurred.
        created_at (DateTimeField): Timestamp when the expense was recorded.
        created_by (ForeignKey): User who created the expense record.
        approval_status (CharField): Current approval state ('pending', 'approved', 'rejected').

    Methods:
        __str__(): String representation showing category, amount, and approval status.
    """
    
    tenant = models.ForeignKey(settings.TENANT_MODEL, on_delete=models.CASCADE)
    category = models.CharField(max_length=100)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    description = models.TextField()
    date = models.DateField()
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)

    APPROVAL_STATUS_CHOICES = [
        ("pending", "Pending"),
        ("approved", "Approved"),
        ("rejected", "Rejected"),
    ]
    approval_status = models.CharField(max_length=10, choices=APPROVAL_STATUS_CHOICES, default="pending")

    def __str__(self):
        return f"{self.category} - {self.amount} ({self.approval_status})"
    

class Notification(models.Model):
    """
    Stores notifications sent to users.

    Attributes:
        user (ForeignKey): Recipient user of the notification.
        message (TextField): Notification content.
        is_read (BooleanField): Flag indicating if the notification has been read.
        created_at (DateTimeField): Timestamp when notification was created.

    Methods:
        __str__(): String representation showing user and read status.
    """
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="notifications")
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Notification for {self.user.username} - Read: {self.is_read}"
