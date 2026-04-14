from celery.schedules import crontab

'''This ensures invoices are automatically created every day.'''
CELERY_BEAT_SCHEDULE = {
    "generate_recurring_invoices_daily": {
        "task": "users.tasks.run_recurring_invoice_generation",
        "schedule": crontab(hour=0, minute=0),  # Runs daily at midnight
    },
}


'''
celery -A your_project_name worker --loglevel=info
celery -A your_project_name beat --loglevel=info

Now, recurring invoices will be generated daily! 🎉
'''

CELERY_BEAT_SCHEDULE["send_invoice_reminders_daily"] = {
    "task": "users.tasks.run_invoice_reminder_task",
    "schedule": crontab(hour=9, minute=0),  # Runs every day at 9 AM
}

'''
celery -A your_project_name worker --loglevel=info
celery -A your_project_name beat --loglevel=info

Now, recurring invoices will be generated daily! 🎉
'''