from datetime import datetime, timedelta
from django.utils.timezone import now
from django.conf import settings
from django.db.models import Sum, F, Q
from django.contrib.auth import authenticate, login

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import  IsAuthenticated
from rest_framework_simplejwt.authentication import JWTAuthentication

from .models import Invoice, Expense
from .permissions import IsAdminUser

from django.conf import settings
from django.apps import apps

Client = apps.get_model(settings.CLIENT_MODEL)
Tenant = apps.get_model(settings.TENANT_MODEL)

# ==========================
# Dashboard (Admin Only)
# ==========================

class DashboardAPIView(APIView):
    """
    API endpoint for Admin Dashboard.

    Authentication:
        Uses JWTAuthentication.
    Permissions:
        Only accessible to authenticated users with admin privileges (IsAdminUser).

    Functionality:
        - Retrieves financial summaries such as total revenue from paid invoices,
          total approved expenses, and calculates net profit.
        - Counts total pending invoices.
        - Fetches latest 5 invoices and expenses.
        - Provides monthly invoice and expense trends for last 6 months.
        - Provides expense category distribution.

    Response:
        JSON object containing:
            total_revenue, total_expenses, net_profit, total_pending,
            recent_invoices, recent_expenses, monthly_data, expense_distribution
    """
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated, IsAdminUser]

    def get(self, request):
        tenant = request.user.userprofile.tenant

        # ✅ Calculate Financial Summary (Exclude Rejected Expenses)
        total_revenue = (
            Invoice.objects.filter(tenant=tenant, status="paid")
            .annotate(total_amount=Sum(F("items__unit_price") * F("items__quantity")))
            .aggregate(Sum("total_amount"))["total_amount__sum"] or 0
        )

        total_expenses = (
            Expense.objects.filter(tenant=tenant, approval_status="approved")  # ✅ Exclude rejected expenses
            .aggregate(Sum("amount"))["amount__sum"] or 0
        )

        net_profit = total_revenue - total_expenses
        total_pending = Invoice.objects.filter(tenant=tenant, status="pending").count()

        # ✅ Fetch Recent Invoices
        recent_invoices = (
            Invoice.objects.filter(tenant=tenant)
            .order_by("-created_at")[:5]
            .values("id", "client__name", "status")
        )

        # ✅ Fetch Recent Expenses (Exclude Rejected)
        recent_expenses = (
            Expense.objects.filter(tenant=tenant, approval_status="approved")  # ✅ Only approved expenses
            .order_by("-created_at")[:5]
            .values("id", "category", "amount", "date")
        )

        # ✅ Monthly Invoice vs Expense Trends (Last 6 Months)
        monthly_data = []
        for month in range(1, 7):  # Last 6 months
            invoices_sum = (
                Invoice.objects.filter(tenant=tenant, created_at__month=month)
                .annotate(total_amount=Sum(F("items__unit_price") * F("items__quantity")))
                .aggregate(Sum("total_amount"))["total_amount__sum"] or 0
            )

            expenses_sum = (
                Expense.objects.filter(tenant=tenant, created_at__month=month, approval_status="approved")  # ✅ Exclude rejected
                .aggregate(Sum("amount"))["amount__sum"] or 0
            )

            monthly_data.append({"month": f"Month {month}", "invoices": invoices_sum, "expenses": expenses_sum})

        # ✅ Expense Category Distribution (Exclude Rejected)
        expense_distribution = (
            Expense.objects.filter(tenant=tenant, approval_status="approved")  # ✅ Only approved
            .values("category")
            .annotate(amount=Sum("amount"))
        )

        return Response({
            "total_revenue": total_revenue,
            "total_expenses": total_expenses,
            "net_profit": net_profit,
            "total_pending": total_pending,
            "recent_invoices": list(recent_invoices),
            "recent_expenses": list(recent_expenses),
            "monthly_data": monthly_data,
            "expense_distribution": list(expense_distribution),
        })
        
class UserDashboardAPIView(APIView):
    """
    API endpoint for User Dashboard.

    Authentication:
        Uses JWTAuthentication.
    Permissions:
        Accessible to any authenticated user.

    Functionality:
        - Provides financial summaries specific to the logged-in user such as total paid and pending invoices,
          total approved expenses, last month's revenue, expenses, and profit.
        - Returns last 5 assigned invoices and recent 5 expenses.

    Response:
        JSON object containing:
            summary (financial aggregates),
            invoices (recent assigned invoices),
            expenses (recent expenses)
    """
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user

        # ✅ Identify last month's date range
        today = datetime.today()
        first_day_last_month = (today.replace(day=1) - timedelta(days=1)).replace(day=1)
        last_day_last_month = today.replace(day=1) - timedelta(days=1)

        # ✅ Total Paid Invoice Amount (Revenue)
        total_paid = (
            Invoice.objects.filter(assigned_users=user, status="paid")
            .annotate(total_amount=Sum(F("items__unit_price") * F("items__quantity")))
            .aggregate(Sum("total_amount"))["total_amount__sum"] or 0
        )

        # ✅ Total Pending Invoice Amount
        total_pending_amount = (
            Invoice.objects.filter(assigned_users=user, status="pending")
            .annotate(total_amount=Sum(F("items__unit_price") * F("items__quantity")))
            .aggregate(Sum("total_amount"))["total_amount__sum"] or 0
        )

        # ✅ Count of Pending Invoices
        total_pending_invoices = Invoice.objects.filter(assigned_users=user, status="pending").count()

        # ✅ Total Approved Expenses
        total_expenses = (
            Expense.objects.filter(created_by=user, approval_status="approved")
            .aggregate(Sum("amount"))["amount__sum"] or 0
        )

        # ✅ Last Month's Revenue
        last_month_revenue = (
            Invoice.objects.filter(
                assigned_users=user, 
                status="paid", 
                created_at__range=[first_day_last_month, last_day_last_month]
            )
            .annotate(total_amount=Sum(F("items__unit_price") * F("items__quantity")))
            .aggregate(Sum("total_amount"))["total_amount__sum"] or 0
        )

        # ✅ Last Month's Expenses
        last_month_expenses = (
            Expense.objects.filter(
                created_by=user, 
                approval_status="approved", 
                date__range=[first_day_last_month, last_day_last_month]
            )
            .aggregate(Sum("amount"))["amount__sum"] or 0
        )

        # ✅ Last Month's Profit
        last_month_profit = last_month_revenue - last_month_expenses

        # ✅ Fetch Assigned Invoices (Last 5)
        assigned_invoices = Invoice.objects.filter(assigned_users=user).order_by("-created_at").values(
            "id", "client__name", "invoice_number", "status"
        )[:5]

        # ✅ Fetch Recent Expenses (Last 5)
        recent_expenses = (
            Expense.objects.filter(created_by=user, approval_status="approved")
            .order_by("-created_at")
            .values("id", "category", "amount", "date")
        )[:5]

        return Response({
            "summary": {
                "total_paid": total_paid,
                "total_pending_amount": total_pending_amount,
                "total_pending_invoices": total_pending_invoices,
                "total_expenses": total_expenses,
                "last_month_revenue": last_month_revenue,
                "last_month_expenses": last_month_expenses,
                "last_month_profit": last_month_profit,
            },
            "invoices": list(assigned_invoices),
            "expenses": list(recent_expenses),
        })

class InvoiceStatusBreakdownView(APIView):
    """
    API endpoint providing invoice counts by status (paid, pending, overdue).

    Authentication:
        Uses JWTAuthentication.
    Permissions:
        Accessible to any authenticated user.

    Functionality:
        - Returns the count of invoices in each status category for the tenant of the logged-in user.

    Response:
        JSON object containing:
            paid_invoices (int),
            pending_invoices (int),
            overdue_invoices (int)
    """
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        tenant = request.user.userprofile.tenant  # Get the tenant of the logged-in user

        # ✅ Fetch invoice counts for each status
        paid_count = Invoice.objects.filter(tenant=tenant, status="paid").count()
        pending_count = Invoice.objects.filter(tenant=tenant, status="pending").count()
        overdue_count = Invoice.objects.filter(tenant=tenant, status="overdue").count()

        # print(f"📊 Invoice Counts -> Paid: {paid_count}, Pending: {pending_count}, Overdue: {overdue_count}")  # ✅ Debugging

        return Response({
            "paid_invoices": paid_count,
            "pending_invoices": pending_count,
            "overdue_invoices": overdue_count
        })




class MonthlyIncomeExpenseView(APIView):
    """
    API endpoint for monthly and yearly income and expense summary.

    Authentication:
        Uses JWTAuthentication.
    Permissions:
        Only accessible to authenticated admin users (IsAdminUser).

    Query Parameters:
        - year (optional): Integer year to filter data (default is current year).
        - month (optional): Integer month to filter data for a specific month.

    Functionality:
        - Computes monthly income from paid invoices and approved expenses.
        - Calculates net profit per month.
        - Aggregates total income, expense, and profit for the year or specific month.

    Response:
        JSON object containing:
            year (int),
            monthly_report (list of dicts with income, expense, net_profit),
            yearly_summary (dict with total_income, total_expense, total_profit)
    """
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated, IsAdminUser]

    def get(self, request):
        tenant = request.user.userprofile.tenant
        year = int(request.query_params.get("year", now().year))  # Convert to int
        month = request.query_params.get("month", None)

        filters = {"tenant": tenant, "created_at__year": year}
        expense_filters = {"tenant": tenant, "date__year": year, "approval_status": "approved"}

        if month:
            filters["created_at__month"] = int(month)
            expense_filters["date__month"] = int(month)

        # ✅ Compute Income from Paid Invoices
        invoices = (
            Invoice.objects.filter(**filters, status="paid")
            .values("created_at__month")
            .annotate(total_income=Sum(F("items__unit_price") * F("items__quantity")))
        )

        # ✅ Compute Expenses
        expenses = (
            Expense.objects.filter(**expense_filters)
            .values("date__month")
            .annotate(total_expense=Sum("amount"))
        )

        # ✅ Prepare Data
        monthly_data = []
        for m in range(1, 13) if not month else [int(month)]:
            income = next((item["total_income"] for item in invoices if item["created_at__month"] == m), 0)
            expense = next((item["total_expense"] for item in expenses if item["date__month"] == m), 0)
            net_profit = income - expense  # ✅ Compute Profit

            monthly_data.append({
                "month": m,
                "income": income,
                "expense": expense,
                "net_profit": net_profit
            })

        # ✅ Debugging: Print data
        # print(f"📊 Year: {year}, Month: {month or 'All'}, Data: {monthly_data}")

        total_income = sum(item["income"] for item in monthly_data)
        total_expense = sum(item["expense"] for item in monthly_data)
        total_profit = total_income - total_expense

        return Response({
            "year": year,
            "monthly_report": monthly_data,
            "yearly_summary": {
                "total_income": total_income,
                "total_expense": total_expense,
                "total_profit": total_profit
            }
        })
