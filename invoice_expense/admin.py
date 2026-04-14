from django.contrib import admin
from .models import Invoice, InvoiceItem, Expense, Notification
# ========================
# Invoice Admin
# ========================
class InvoiceItemInline(admin.TabularInline):
    """
    Inline admin interface for managing InvoiceItem objects directly within
    the Invoice admin panel.
    
    - Displays item fields in a tabular layout.
    - 'extra = 1' adds one empty form for new item by default.
    - 'readonly_fields' ensures these values are view-only.
    """
    model = InvoiceItem
    extra = 1
    readonly_fields = ("unit_price", "quantity")

@admin.register(Invoice)
class InvoiceAdmin(admin.ModelAdmin):
    """
    Admin configuration for the Invoice model.
    
    Features:
    - Lists invoice details including number, client, status, total, due date.
    - Enables filtering and searching invoices.
    - Shows associated InvoiceItems inline.
    - Restricts modification of some fields using 'readonly_fields'.
    - Uses 'fieldsets' to group and organize fields in the admin form.
    """
    
    list_display = ("invoice_number", "client", "status", "total_amount", "due_date", "created_at")
    list_filter = ("status", "due_date")
    search_fields = ("invoice_number", "client__name")
    inlines = [InvoiceItemInline]
    readonly_fields = ("invoice_number", "total_amount", "created_at")
    filter_horizontal = ("assigned_users",)

    fieldsets = (
        ("Invoice Details", {
            "fields": ("tenant", "client", "status", "due_date", "assigned_users")
        }),
        ("Amount", {
            "fields": ("total_amount",)
        }),
    )
    
    def total_amount(self, obj):
        """
        Computes the total amount for the invoice by multiplying
        quantity and unit price for each item in the invoice.
        """
        return sum(item.unit_price * item.quantity for item in obj.items.all())

    total_amount.short_description = "Total Amount"

# ========================
# Expense Admin
# ========================
@admin.register(Expense)
class ExpenseAdmin(admin.ModelAdmin):
    """
    Admin configuration for the Expense model.
    
    Features:
    - Lists key expense details including category, amount, and creator.
    - Enables filtering by approval status.
    - Uses a fieldset to group form fields in the admin interface.
    - 'created_at' is read-only.
    """
    list_display = ("category", "amount", "get_status", "created_at", "created_by")
    list_filter = ("approval_status",)
    search_fields = ("category", "description")
    readonly_fields = ("created_at",)

    fieldsets = (
        ("Expense Details", {
            "fields": ("category", "amount", "description", "date", "approval_status", "created_by", "created_at")
        }),
    )

    @admin.display(description="Status")
    def get_status(self, obj):
        """
        Returns the approval status of the expense for display.
        """
        return obj.approval_status

# ========================
# Notification Admin
# ========================
@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    """
    Admin configuration for the Notification model.
    
    Features:
    - Lists notifications with user, message, read status, and timestamp.
    - Enables filtering by read/unread status.
    - Allows searching by username or message content.
    """
    list_display = ("user", "message", "is_read", "created_at")
    list_filter = ("is_read",)
    search_fields = ("user__username", "message")

