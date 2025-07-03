from datetime import timedelta
from django.utils.timezone import now
from django.conf import settings
from django.db.models import Q
from django.contrib.auth.models import User
from django.http import StreamingHttpResponse, Http404

from rest_framework import generics, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.authentication import JWTAuthentication

from .models import Invoice, InvoiceItem
from .serializers import InvoiceSerializer
from .utils import generate_invoice_pdf
from .permissions import CanCreateInvoice

from django.apps import apps

Client = apps.get_model(settings.CLIENT_MODEL)
Tenant = apps.get_model(settings.TENANT_MODEL)

# ==========================
# Admin: List and Create Invoices
# ==========================

class InvoiceListCreateView(generics.ListCreateAPIView):
    """
    GET: List invoices filtered by tenant and user role.
         Admins see all tenant invoices,
         Non-admins see only invoices assigned to them.
    POST: Create a new invoice with related items and assigned users.
    """
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated, CanCreateInvoice]
    serializer_class = InvoiceSerializer

    def get_queryset(self):
        """
        Return invoices belonging to the user's tenant.
        Non-admin users only see invoices assigned to them.
        """
        
        user_profile = self.request.user.userprofile
        tenant = user_profile.tenant
        invoices = Invoice.objects.filter(tenant=tenant)

        if user_profile.role != "admin":
            invoices = invoices.filter(assigned_users=self.request.user)

        return self.apply_filters(invoices)

    def apply_filters(self, invoices):
        """
        Apply query parameter filters:
        - client_name (partial match)
        - user_name (partial match)
        - month (invoice creation month)
        - year (invoice creation year)
        - status (exact match, case-insensitive)
        """
        client_name = self.request.query_params.get("client_name")
        if client_name:
            invoices = invoices.filter(client__name__icontains=client_name)

        user_name = self.request.query_params.get("user_name")
        if user_name:
            invoices = invoices.filter(assigned_users__username__icontains=user_name)

        month = self.request.query_params.get("month")
        if month and month.isdigit():
            invoices = invoices.filter(created_at__month=int(month))

        year = self.request.query_params.get("year")
        if year and year.isdigit():
            invoices = invoices.filter(created_at__year=int(year))

        status_filter = self.request.query_params.get("status")
        if status_filter:
            invoices = invoices.filter(status__iexact=status_filter)

        return invoices.distinct()

    def create(self, request, *args, **kwargs):
        """
        Create a new invoice:
        - Validate tenant and client relationship.
        - For non-admin users, restrict assigned users to self.
        - Create invoice items based on request data.
        """
        user_profile = request.user.userprofile
        tenant_id = request.data.get("tenant")
        client_id = request.data.get("client")
        assigned_user_ids = request.data.get("assigned_users", [])
        invoice_status = request.data.get("status", "pending")
        items_data = request.data.get("items", [])

        if not tenant_id:
            return Response({"error": "Tenant ID is required."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            tenant = Tenant.objects.get(id=tenant_id)
            client = Client.objects.get(id=client_id, tenant=tenant)
        except Tenant.DoesNotExist:
            return Response({"error": "Invalid tenant ID."}, status=status.HTTP_400_BAD_REQUEST)
        except Client.DoesNotExist:
            return Response({"error": "Client does not exist in this tenant."}, status=status.HTTP_400_BAD_REQUEST)

        assigned_users = User.objects.filter(id__in=assigned_user_ids) if assigned_user_ids else []
        if user_profile.role != "admin":
            assigned_users = [request.user]

        invoice = Invoice.objects.create(
            tenant=tenant,
            client=client,
            invoice_number=request.data.get("invoice_number"),
            due_date=request.data.get("due_date"),
            status=invoice_status
        )
        invoice.assigned_users.set(assigned_users)

        for item_data in items_data:
            InvoiceItem.objects.create(invoice=invoice, **item_data)

        serializer = self.get_serializer(invoice)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

# ==========================
# Public-Safe GET View for All Authenticated Users
# ==========================

class InvoiceListOnlyView(generics.ListAPIView):
    """
    GET: List invoices with filters.
    Admins see all invoices in their tenant.
    Non-admins see only invoices assigned to them.
    """
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]
    serializer_class = InvoiceSerializer

    def get_queryset(self):
        """
        Return invoices filtered by tenant and user role.
        """
        user_profile = self.request.user.userprofile
        tenant = user_profile.tenant
        invoices = Invoice.objects.filter(tenant=tenant)

        if user_profile.role != "admin":
            invoices = invoices.filter(assigned_users=self.request.user)

        return self.apply_filters(invoices)

    def apply_filters(self, invoices):
        """
        Apply query filters like client_name, user_name, month, year, and status.
        """
        client_name = self.request.query_params.get("client_name")
        if client_name:
            invoices = invoices.filter(client__name__icontains=client_name)

        user_name = self.request.query_params.get("user_name")
        if user_name:
            invoices = invoices.filter(assigned_users__username__icontains=user_name)

        month = self.request.query_params.get("month")
        if month and month.isdigit():
            invoices = invoices.filter(created_at__month=int(month))

        year = self.request.query_params.get("year")
        if year and year.isdigit():
            invoices = invoices.filter(created_at__year=int(year))

        status_filter = self.request.query_params.get("status")
        if status_filter:
            invoices = invoices.filter(status__iexact=status_filter)

        return invoices.distinct()

# =====================
# Invoice Detail View
# =====================

class InvoiceDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    GET, PUT, PATCH, DELETE an invoice by ID.
    Admins can access all tenant invoices.
    Non-admins only access invoices assigned to them.
    """
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]
    serializer_class = InvoiceSerializer

    def get_queryset(self):
        user_profile = self.request.user.userprofile
        tenant = user_profile.tenant

        if user_profile.role == "admin":
            return Invoice.objects.filter(tenant=tenant)
        return Invoice.objects.filter(assigned_users=self.request.user)

# =====================
# PDF Generation View
# =====================

class InvoicePDFView(APIView):
    """
    Generate and stream PDF file for a specific invoice.
    Only accessible by admin or assigned users.
    """
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request, invoice_id):
        try:
            invoice = Invoice.objects.get(id=invoice_id)
            user_profile = request.user.userprofile
            
            # Permission check: admin or assigned user only
            if user_profile.role != "admin" and request.user not in invoice.assigned_users.all():
                return Response({"error": "Unauthorized access to this invoice."}, status=403)
            
            # Generate PDF content as bytes stream
            pdf_buffer = generate_invoice_pdf(invoice_id)
            response = StreamingHttpResponse(pdf_buffer, content_type="application/pdf")
            
            # Inline display with filename containing invoice number
            response["Content-Disposition"] = f'inline; filename="invoice_{invoice.invoice_number}.pdf"'
            
            # CORS headers for frontend (adjust origin as needed)
            response["Access-Control-Allow-Origin"] = "http://localhost:5173"
            response["Access-Control-Allow-Credentials"] = "true"
            response["Access-Control-Allow-Methods"] = "GET, OPTIONS"
            response["Access-Control-Allow-Headers"] = "Authorization, Content-Type"

            return response

        except Invoice.DoesNotExist:
            raise Http404("Invoice not found")
        except Exception as e:
            return Response({"error": str(e)}, status=500)

# ======================
# Last Invoice Number View
# ======================

class LastInvoiceView(APIView):
    """
    Return the last invoice created in the tenant.
    If none found, return a default invoice number based on tenant name.
    """
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user_profile = request.user.userprofile
        tenant = user_profile.tenant

        invoices = Invoice.objects.filter(tenant=tenant)
        if user_profile.role != "admin":
            invoices = invoices.filter(assigned_users=request.user)

        last_invoice = invoices.order_by("-created_at").first()

        if last_invoice:
            serializer = InvoiceSerializer(last_invoice)
            return Response(serializer.data, status=200)
        else:
            first_invoice_number = f"{tenant.name.upper()}-1001"
            return Response({"invoice_number": first_invoice_number}, status=200)
