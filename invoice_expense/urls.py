from django.urls import path
from invoice_expense.views import UnreadNotificationsCountView, UserNotificationsView
from invoice_expense.invoice_views import InvoiceListCreateView, InvoiceDetailView, InvoicePDFView, LastInvoiceView, InvoiceListOnlyView
from invoice_expense.expense_views import ExpenseListCreateView, ExpenseDetailView, ApproveRejectExpenseView
from invoice_expense.dashboard_views import DashboardAPIView, UserDashboardAPIView, InvoiceStatusBreakdownView  # ✅ Added UserDashboardAPIView

urlpatterns = [

    # ==========================
    # Invoice Management
    # ==========================
    path("invoices/", InvoiceListOnlyView.as_view(), name="invoice-list"),  # For all authenticated users
    path("invoices/manage/", InvoiceListCreateView.as_view(), name="invoice-create"),  # Admins only
    # path('invoices/', InvoiceListCreateView.as_view(), name='invoice-list-create'),  # Create & List Invoices
    # path('invoices/all/', InvoiceListCreateView.as_view(), name='invoice-list'),  # List Invoices (Admin/User-specific)
    path('invoices/<int:pk>/', InvoiceDetailView.as_view(), name='invoice-detail'),  # View, Update & Delete Invoice
    path("invoices/<int:invoice_id>/pdf/", InvoicePDFView.as_view(), name="invoice_pdf"),
    path("invoices/last/", LastInvoiceView.as_view(), name="last-invoice"),

    # ==========================
    # Expense Management
    # ==========================
    path('expenses/', ExpenseListCreateView.as_view(), name='expense-list-create'),  # Create & List Expenses
    path('expenses/<int:pk>/', ExpenseDetailView.as_view(), name='expense-detail'),  # View, Update & Delete Expense
    path("expenses/<int:expense_id>/approve-reject/", ApproveRejectExpenseView.as_view(), name="approve-reject-expense"),
    
    # ==========================
    # Admin Dashboards 
    # ==========================
    path('dashboard/', DashboardAPIView.as_view(), name='dashboard'),  # ✅ Admin Dashboard
    
    path('invoice-status-breakdown/', InvoiceStatusBreakdownView.as_view(), name='invoice-status-breakdown'),
    
    # ==========================
    # Notification 
    # ==========================
    path("notifications/", UserNotificationsView.as_view(), name="user-notifications"),  # ✅ Fetch notifications
    path("notifications/unread-count/", UnreadNotificationsCountView.as_view(), name="unread-notifications-count"),
    # ==========================
    # User Dashboards
    # ==========================
    path('user-dashboard/', UserDashboardAPIView.as_view(), name='user-dashboard'),  # ✅ User Dashboard    
    
]

from .dashboard_views import MonthlyIncomeExpenseView

urlpatterns += [
    path('monthly-income-expense/', MonthlyIncomeExpenseView.as_view(), name='monthly-income-expense'),
]