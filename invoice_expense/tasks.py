from celery import shared_task
from invoice_expense.utils import generate_recurring_invoices, send_pending_invoice_reminders

@shared_task
def run_recurring_invoice_generation():
    """
    Celery task to generate recurring invoices.

    This task calls the utility function `generate_recurring_invoices` which
    processes all recurring invoice rules and creates new invoices accordingly.
    It is meant to be scheduled and run asynchronously to automate invoice generation.
    
    Returns:
        str: Confirmation message after processing recurring invoices.
    """
    
    generate_recurring_invoices()
    return "Recurring invoices processed successfully!"


@shared_task
def run_invoice_reminder_task():
    """
    Celery task to send reminders for pending invoices.

    This task calls `send_pending_invoice_reminders` to identify invoices
    that are unpaid or nearing due date, and sends reminder notifications 
    to clients and assigned users.

    It is designed to run asynchronously on a schedule to improve timely payments.

    Returns:
        str: Confirmation message after sending reminders.
    """
    
    send_pending_invoice_reminders()
    return "Pending invoice reminders sent!"
