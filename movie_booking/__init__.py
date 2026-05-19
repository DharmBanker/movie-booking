"""
Movie Booking Django Project
Initializes Celery app so it's loaded when Django starts.
"""

# Import Celery app to ensure it's initialized when Django starts.
# This is required for the @shared_task decorator to work correctly.
from .celery import app as celery_app

__all__ = ('celery_app',)
