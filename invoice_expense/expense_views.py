from django.utils.timezone import now
from django.conf import settings
from django.db.models import Sum, Q
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login

from rest_framework import generics, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import  IsAuthenticated
from rest_framework_simplejwt.authentication import JWTAuthentication

from .models import Expense, Notification
from .serializers import ExpenseSerializer
from .utils import generate_invoice_pdf, send_invoice_reminder
from users.permissions import IsAdminUser

from django.conf import settings
from django.apps import apps


Client = apps.get_model(settings.CLIENT_MODEL)
Tenant = apps.get_model(settings.TENANT_MODEL)

class ExpenseListCreateView(generics.ListCreateAPIView):
    """✅ Users create expenses (pending approval), Admins' expenses auto-approve. Admins are notified of pending expenses."""
    """
    API endpoint to list and create expenses for tenants.

    - Users can create expenses which default to 'pending' approval.
    - Admin users' expenses are automatically approved.
    - Admin users see all expenses within their tenant.
    - Regular users see only their own approved and pending expenses.
    - Admins can filter expenses by approval status and creator.
    - Supports filtering by month, year, and category.
    - Admins are notified when users submit new expenses requiring approval.
    """
    
    authentication_classes = [JWTAuthentication]
    serializer_class = ExpenseSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """✅ Admins see all expenses; Users see only their own `approved` + `pending` expenses."""
        """
        Returns a queryset of expenses filtered by user role and query parameters.

        - Admins see all expenses for their tenant.
        - Users see their own expenses with status 'approved' or 'pending'.
        - Optional filters (admins only): approval_status, created_by.
        - Optional filters (all): month, year, category.
        """
        user = self.request.user
        queryset = Expense.objects.filter(tenant=user.userprofile.tenant)

        if user.userprofile.role != "admin":
            # ✅ Users only see their own "approved" & "pending" expenses (NOT rejected)
            queryset = queryset.filter(created_by=user).filter(Q(approval_status="approved") | Q(approval_status="pending"))

        # ✅ Allow filtering by approval_status (Only for admins)
        approval_status = self.request.query_params.get("approval_status")
        if approval_status and user.userprofile.role == "admin":
            queryset = queryset.filter(approval_status=approval_status)

        # ✅ Allow filtering by created_by (Only for admins)
        created_by = self.request.query_params.get("created_by")
        if created_by and user.userprofile.role == "admin":
            queryset = queryset.filter(created_by__username=created_by)

        # ✅ Allow filtering by month and year
        month = self.request.query_params.get("month")
        year = self.request.query_params.get("year")
        if month and year:
            queryset = queryset.filter(date__month=month, date__year=year)

        # ✅ Allow filtering by category (both fixed & custom)
        category = self.request.query_params.get("category")
        if category:
            queryset = queryset.filter(Q(category=category) | Q(category__iexact=category))

        return queryset

    def list(self, request, *args, **kwargs):
        """✅ Override list method to calculate correct total expenses for admins & users."""
        """
        Overrides the default list method to include total expenses in the response.

        - Calculates the sum of approved expenses for the tenant.
        - Users see total of their own approved expenses.
        - Supports category filtering when calculating totals.
        """
        response = super().list(request, *args, **kwargs)

        user = request.user
        queryset = Expense.objects.filter(tenant=user.userprofile.tenant, approval_status="approved")

        if user.userprofile.role != "admin":
            # ✅ Users see only their own approved expenses
            queryset = queryset.filter(created_by=user)

        # ✅ Apply category filter when calculating total expenses
        category = request.query_params.get("category")
        if category:
            queryset = queryset.filter(Q(category=category) | Q(category__iexact=category))

        total_expenses = queryset.aggregate(total_amount=Sum("amount"))["total_amount"] or 0

        response.data = {
            "total_expenses": total_expenses,
            "expenses": response.data
        }
        return Response(response.data)

    def perform_create(self, serializer):
        """✅ Users create expenses (default: pending). Admin expenses auto-approve. Admin gets notified when a user submits an expense."""
        """
        Creates an expense entry.

        - For admin users, the expense is auto-approved.
        - For regular users, expense status defaults to 'pending'.
        - Notifies all tenant admins when a user submits a new expense pending approval.
        """
        user = self.request.user
        tenant = user.userprofile.tenant

        if not tenant:
            return Response({"error": "User does not belong to a tenant."}, status=status.HTTP_400_BAD_REQUEST)

        # ✅ Auto-approve expenses if the creator is an admin
        approval_status = "approved" if user.userprofile.role == "admin" else "pending"

        expense = serializer.save(tenant=tenant, created_by=user, approval_status=approval_status)

        if user.userprofile.role != "admin":
            # ✅ Notify all admins of this tenant about a new pending expense
            admins = User.objects.filter(userprofile__tenant=tenant, userprofile__role="admin")
            for admin in admins:
                Notification.objects.create(
                    user=admin,
                    message=f"New expense '{expense.category}' (${expense.amount}) requires approval."
                )


class ApproveRejectExpenseView(APIView):
    """
    API endpoint for admins to approve or reject expenses.

    - Only accessible to authenticated admin users.
    - Updates the approval_status of the specified expense.
    - Sends notification to the expense creator about approval or rejection.
    """
    
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated, IsAdminUser]

    def post(self, request, expense_id):
        try:
            expense = Expense.objects.get(id=expense_id, tenant=request.user.userprofile.tenant)
            status = request.data.get("approval_status")

            if status not in ["approved", "rejected"]:
                return Response({"error": "Invalid approval status."}, status=status.HTTP_400_BAD_REQUEST)

            # ✅ Update the expense status
            expense.approval_status = status
            expense.save()

            # ✅ Notify User About Expense Approval/Rejection
            Notification.objects.create(
                user=expense.created_by,
                message=f"Your expense '{expense.category}' (${expense.amount}) has been {status}."
            )

            return Response({"message": f"Expense {status} successfully, and user has been notified."})

        except Expense.DoesNotExist:
            return Response({"error": "Expense not found."}, status=status.HTTP_404_NOT_FOUND)


class ExpenseDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    API endpoint to retrieve, update, or delete a single expense.

    - Admins can manage any expense within their tenant.
    - Users can only manage their own expenses.
    """
    
    authentication_classes = [JWTAuthentication]
    serializer_class = ExpenseSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Admins can manage all expenses, users can only view their own expenses."""
        user_profile = self.request.user.userprofile
        if user_profile.role == "admin":
            return Expense.objects.filter(tenant=user_profile.tenant)
        return Expense.objects.filter(created_by=self.request.user)
