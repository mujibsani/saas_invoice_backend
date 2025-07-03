from django.apps import AppConfig


class InvoiceExpenseConfig(AppConfig):
    """
    Configuration class for the 'invoice_expense' Django app.

    Attributes:
        default_auto_field (str): Specifies the default type of primary key
                                  field to use for models in this app.
                                  Here, it's set to BigAutoField for large IDs.
        name (str): The full Python path to the application, used by Django
                    to identify and configure the app.
    """
    
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'invoice_expense'
