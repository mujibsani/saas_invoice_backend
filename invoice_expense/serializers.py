from django.conf import settings
from django.apps import apps
from django.contrib.auth import get_user_model
from rest_framework import serializers
from django.db import models

User = get_user_model()

Invoice = apps.get_model(getattr(settings, "INVOICE_MODEL", "invoice_expense.Invoice"))
InvoiceItem = apps.get_model(getattr(settings, "INVOICE_ITEM_MODEL", "invoice_expense.InvoiceItem"))
Expense = apps.get_model(getattr(settings, "EXPENSE_MODEL", "invoice_expense.Expense"))
Notification = apps.get_model(getattr(settings, "NOTIFICATION_MODEL", "invoice_expense.Notification"))
Client = apps.get_model(settings.CLIENT_MODEL)
Tenant = apps.get_model(settings.TENANT_MODEL)

# ==========================
# Invoice Serializers
# ==========================

class InvoiceItemSerializer(serializers.ModelSerializer):
    """
    Serializer for individual invoice items.

    Fields:
        - id: Unique identifier of the invoice item.
        - name: Name of the item.
        - description: Detailed description of the item.
        - quantity: Number of units for this item.
        - unit_price: Price per unit of the item.
    """
    class Meta:
        model = InvoiceItem
        fields = ["id", "name", "description", "quantity", "unit_price"]

class InvoiceSerializer(serializers.ModelSerializer):
    """
    Serializer for Invoice model including nested items and assigned users.

    Supports creating and updating invoices with related invoice items.

    Fields:
        - id: Unique identifier of the invoice.
        - tenant: Reference to the tenant owning the invoice.
        - tenant_name: Read-only name of the tenant.
        - client: Reference to the client associated with the invoice.
        - client_name: Read-only name of the client.
        - invoice_number: Unique invoice number (read-only).
        - due_date: Payment due date.
        - status: Invoice status.
        - assigned_users: Users assigned to this invoice.
        - items: List of invoice items.
        - total_amount: Computed total amount of the invoice (read-only).
        - created_at: Timestamp when the invoice was created (read-only).
    """
    client = serializers.PrimaryKeyRelatedField(queryset=Client.objects.all(), required=True)
    client_name = serializers.ReadOnlyField(source="client.name")
    tenant_name = serializers.ReadOnlyField(source="tenant.name")
    assigned_users = serializers.PrimaryKeyRelatedField(queryset=User.objects.all(), many=True, required=False)
    items = InvoiceItemSerializer(many=True, required=True)
    total_amount = serializers.SerializerMethodField()

    class Meta:
        model = Invoice
        fields = [
            "id",
            "tenant",
            "tenant_name",
            "client",
            "client_name",
            "invoice_number",
            "due_date",
            "status",
            "assigned_users",
            "items",
            "total_amount",
            "created_at",
        ]
        read_only_fields = ["id", "created_at", "total_amount", "invoice_number"]

    def get_total_amount(self, obj):
        """
        Calculate the total amount by summing unit price * quantity for all invoice items.

        Args:
            obj (Invoice): Invoice instance.

        Returns:
            Decimal: Total amount for all related invoice items or 0 if none exist.
        """
        
        return obj.items.aggregate(total=models.Sum(models.F("unit_price") * models.F("quantity")))["total"] or 0

    def create(self, validated_data):
        """
        Create an invoice and its related invoice items.

        Args:
            validated_data (dict): Validated data from the request.

        Returns:
            Invoice: Created Invoice instance.
        """
        
        items_data = validated_data.pop("items", [])
        assigned_users = validated_data.pop("assigned_users", [])

        invoice = Invoice.objects.create(**validated_data)
        invoice.assigned_users.set(assigned_users)

        invoice_items = [InvoiceItem(invoice=invoice, **item_data) for item_data in items_data]
        InvoiceItem.objects.bulk_create(invoice_items)

        return invoice

    def update(self, instance, validated_data):
        """
        Update an invoice instance including related invoice items and assigned users.

        Args:
            instance (Invoice): Existing invoice instance.
            validated_data (dict): Validated update data.

        Returns:
            Invoice: Updated invoice instance.
        """
        items_data = validated_data.pop("items", None)
        assigned_users = validated_data.pop("assigned_users", None)

        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        if assigned_users is not None:
            instance.assigned_users.set(assigned_users)

        instance.save()

        if items_data is not None:
            existing_item_ids = [item["id"] for item in items_data if "id" in item]
            InvoiceItem.objects.filter(invoice=instance).exclude(id__in=existing_item_ids).delete()

            for item_data in items_data:
                item_id = item_data.get("id", None)
                if item_id:
                    InvoiceItem.objects.filter(id=item_id, invoice=instance).update(**item_data)
                else:
                    InvoiceItem.objects.create(invoice=instance, **item_data)

        return instance

# ==========================
# Expense Serializers
# ==========================

class ExpenseSerializer(serializers.ModelSerializer):
    """
    Serializer for Expense model including tenant and creator info.

    Fields:
        - id: Unique identifier.
        - tenant: Tenant that owns this expense.
        - tenant_name: Read-only name of the tenant.
        - category: Expense category.
        - amount: Expense amount.
        - description: Details about the expense.
        - date: Date of the expense.
        - created_at: Timestamp when created (read-only).
        - approval_status: Current approval state (read-only).
        - created_by: User who created the expense (read-only).
        - created_by_username: Read-only username of the creator.
    """
    tenant_name = serializers.ReadOnlyField(source="tenant.name")
    created_by_username = serializers.ReadOnlyField(source="created_by.username")

    class Meta:
        model = Expense
        fields = [
            "id", "tenant", "tenant_name", "category", "amount",
            "description", "date", "created_at", "approval_status",
            "created_by", "created_by_username"
        ]
        read_only_fields = ["id", "created_at", "approval_status", "created_by"]

# ==========================
# Notification Serializer
# ==========================

class NotificationSerializer(serializers.ModelSerializer):
    """
    Serializer for user notifications.

    Fields:
        - id: Unique notification identifier.
        - message: Notification message content.
        - is_read: Boolean indicating if the notification has been read.
        - created_at: Timestamp when notification was created.
    """
    class Meta:
        model = Notification
        fields = ["id", "message", "is_read", "created_at"]

# ==========================
# Dashboard Serializers
# ==========================

class SummarySerializer(serializers.Serializer):
    """
    Serializer for financial dashboard summary metrics.

    Fields:
        - total_invoices: Total number of invoices.
        - total_expenses: Sum of all expenses.
        - total_revenue: Total revenue generated.
        - outstanding_payments: Sum of payments not yet received.
    """
    total_invoices = serializers.IntegerField()
    total_expenses = serializers.DecimalField(max_digits=10, decimal_places=2)
    total_revenue = serializers.DecimalField(max_digits=10, decimal_places=2)
    outstanding_payments = serializers.DecimalField(max_digits=10, decimal_places=2)

class InvoiceExpenseTrendSerializer(serializers.Serializer):
    """
    Serializer for representing invoice and expense trends over time.

    Fields:
        - date: Date of the data point.
        - total_invoices: Total invoice amount on the date.
        - total_expenses: Total expense amount on the date.
    """
    date = serializers.DateField()
    total_invoices = serializers.DecimalField(max_digits=10, decimal_places=2)
    total_expenses = serializers.DecimalField(max_digits=10, decimal_places=2)

class ExpenseDistributionSerializer(serializers.Serializer):
    """
    Serializer for expense distribution grouped by category.

    Fields:
        - category: Expense category name.
        - total_expense: Total expense amount in this category.
    """
    category = serializers.CharField()
    total_expense = serializers.DecimalField(max_digits=10, decimal_places=2)

# ==========================
# Recent Activity Serializers
# ==========================

class RecentInvoiceSerializer(serializers.ModelSerializer):
    """
    Serializer for recent invoices shown in dashboard previews.

    Fields:
        - id: Invoice identifier.
        - client_name: Name of the client.
        - amount: Invoice amount.
        - due_date: Payment due date.
        - status: Invoice status.
    """
    client_name = serializers.ReadOnlyField(source='client.name')

    class Meta:
        model = Invoice
        fields = ['id', 'client_name', 'amount', 'due_date', 'status']

class RecentExpenseSerializer(serializers.ModelSerializer):
    """
    Serializer for recent expenses shown in dashboard previews.

    Fields:
        - id: Expense identifier.
        - category: Expense category.
        - amount: Expense amount.
        - date: Date of expense.
        - description: Expense description.
    """
    class Meta:
        model = Expense
        fields = ['id', 'category', 'amount', 'date', 'description']
