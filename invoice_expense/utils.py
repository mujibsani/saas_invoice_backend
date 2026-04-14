from io import BytesIO
from reportlab.pdfgen import canvas
from .models import Invoice
from django.core.mail import send_mail
from django.conf import settings
from django.utils.timezone import now
from datetime import timedelta
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas

from reportlab.lib import colors
from reportlab.lib.utils import ImageReader

def generate_invoice_pdf(invoice_id):
    """Generate a Professional Invoice PDF with a Tenant Logo, Name, and Watermark"""
    invoice = Invoice.objects.get(id=invoice_id)
    buffer = BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4  # Page size

    # ✅ Add Tenant Watermark in Light Grey (on all pages)
    pdf.saveState()
    pdf.setFont("Helvetica-Bold", 40)
    pdf.setFillColor(colors.lightgrey)
    pdf.rotate(35)  # Rotate text for a watermark effect
    pdf.drawString(50, 10, invoice.tenant.name)  # Watermark position
    pdf.restoreState()

    # ✅ Add Tenant Logo (if available)
    logo_x, logo_y = 40, height - 80  # Position logo top-left
    if invoice.tenant.logo:
        logo_path = f"{settings.MEDIA_ROOT}/{invoice.tenant.logo.name}"
        try:
            logo = ImageReader(logo_path)
            pdf.drawImage(logo, logo_x, logo_y, width=100, height=50, mask="auto")
        except:
            pass  # If logo file is missing, ignore the error

    # ✅ Add Tenant Name Next to Logo
    pdf.setFont("Helvetica-Bold", 18)
    pdf.setFillColor(colors.black)
    pdf.drawString(160, height - 50, invoice.tenant.name)  # Align text with logo

    # ✅ Invoice Title (Right Side)
    # pdf.setFont("Helvetica-Bold", 18)
    # pdf.drawString(width - 200, height - 70, "INVOICE")

    # ✅ Invoice Header Information
    pdf.setFont("Helvetica", 12)
    pdf.drawString(width - 200, height - 90, f"Invoice #: {invoice.invoice_number[(len(invoice.invoice_number))-6:]}")
    pdf.drawString(width - 200, height - 110, f"Date: {invoice.created_at.strftime('%Y-%m-%d')}")
    pdf.drawString(width - 200, height - 130, f"Due Date: {invoice.due_date.strftime('%Y-%m-%d')}")
    if invoice.status == 'paid':
        pdf.setFont("Helvetica-Bold", 14)
    pdf.drawString(width - 200, height - 150, f"Status: {invoice.status}")

    # ✅ Client Information Box
    pdf.setFont("Helvetica-Bold", 12)
    pdf.drawString(40, height - 130, "Bill To:")
    pdf.setFont("Helvetica", 12)
    pdf.drawString(40, height - 150, f"Client: {invoice.client.name}")
    pdf.drawString(40, height - 170, f"Email: {invoice.client.email}")
    pdf.drawString(40, height - 190, f"Phone: {invoice.client.phone}")

    # ✅ Table Header
    table_y = height - 230
    pdf.setFont("Helvetica-Bold", 12)
    pdf.setFillColor(colors.white)
    pdf.setStrokeColor(colors.black)
    pdf.setLineWidth(1)
    pdf.rect(40, table_y, width - 80, 25, fill=True, stroke=True)  # Header Background
    pdf.setFillColor(colors.black)
    pdf.drawString(50, table_y + 7, "Item Name")
    pdf.drawString(230, table_y + 7, "Quantity")
    pdf.drawString(310, table_y + 7, "Unit Price")
    pdf.drawString(400, table_y + 7, "Total")

    pdf.line(40, table_y, width - 40, table_y)  # Table Top Border

    # ✅ Invoice Items
    pdf.setFont("Helvetica", 12)
    y = table_y - 25
    for item in invoice.items.all():
        pdf.drawString(50, y, item.name)
        pdf.drawString(230, y, str(item.quantity))
        pdf.drawString(310, y, f"${item.unit_price:.2f}")
        pdf.drawString(400, y, f"${item.quantity * item.unit_price:.2f}")
        y -= 20

    pdf.line(40, y, width - 40, y)  # Line Before Total

    # ✅ Total Amount
    pdf.setFont("Helvetica-Bold", 14)
    pdf.drawString(310, y - 30, "Total Amount:")
    pdf.drawString(400, y - 30, f"${invoice.total_amount():.2f}")

    # ✅ Thank You Message
    pdf.setFont("Helvetica", 12)
    pdf.setFillColor(colors.green)
    pdf.drawString(50, y - 70, "Thank you for your business!")

    # ✅ Save & Return PDF
    pdf.showPage()
    pdf.save()
    buffer.seek(0)
    return buffer


def send_invoice_reminder(invoice_id):
    '''Sends a reminder email to the client.'''
    invoice = Invoice.objects.get(id=invoice_id)
    client = invoice.client

    subject = f"Payment Reminder: Invoice {invoice.invoice_number}"
    message = f"Dear {client.name},\n\nYour invoice of ${invoice.amount} is pending. Please pay before {invoice.due_date}.\n\nThank you!"
    recipient_list = [client.email]

    send_mail(subject, message, settings.EMAIL_HOST_USER, recipient_list)


def generate_recurring_invoices():
    '''This function will run daily to check for invoices that need to be generated.'''
    today = now().date()
    recurring_invoices = Invoice.objects.filter(recurring=True, next_invoice_date=today)

    for invoice in recurring_invoices:
        new_invoice = Invoice.objects.create(
            tenant=invoice.tenant,
            client=invoice.client,
            invoice_number=f"{invoice.invoice_number}-{today.strftime('%Y%m%d')}",
            amount=invoice.amount,
            due_date=today + timedelta(days=7),  # Set new due date
            status="pending",
            recurring=True,
            recurring_period=invoice.recurring_period,
            next_invoice_date=invoice.calculate_next_invoice_date(),
        )
        new_invoice.save()
        
        

def send_pending_invoice_reminders():
    '''Automate email reminders for unpaid invoices.'''
    today = now().date()
    pending_invoices = Invoice.objects.filter(status="pending", due_date__lte=today)

    for invoice in pending_invoices:
        send_invoice_reminder(invoice.id)