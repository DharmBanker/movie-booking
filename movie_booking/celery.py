"""
Celery Application Configuration
Configures Celery with Redis as the message broker for background task processing.
"""

import os
from celery import Celery
from django.conf import settings

# Set the default Django settings module for Celery
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'movie_booking.settings')

# Create the Celery application instance
app = Celery('movie_booking')

# Load configuration from Django settings using the CELERY_ namespace prefix
# All CELERY_* settings in settings.py are automatically picked up
app.config_from_object('django.conf:settings', namespace='CELERY')

# Auto-discover tasks from all installed Django apps
# Celery will look for tasks.py in each app directory
app.autodiscover_tasks(lambda: settings.INSTALLED_APPS)


@app.task(bind=True, ignore_result=True)
def debug_task(self):
    """Debug task to verify Celery is working correctly."""
    print(f'Request: {self.request!r}')
