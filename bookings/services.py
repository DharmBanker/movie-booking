"""
Bookings App — Service Layer

Handles all booking business logic:
- BookingService: Creates bookings, generates references, triggers email tasks
- BookingReferenceGenerator: Generates unique booking reference codes
"""

import logging
import random
import string
from django.db import transaction
from django.db.models import F
from django.utils import timezone

from .models import Booking, BookingEmailLog, Show

logger = logging.getLogger(__name__)


class DuplicatePaymentError(Exception):
    """Raised when a booking with the same payment_id already exists."""
    pass


class BookingReferenceGenerator:
    """Generates unique, human-readable booking reference codes."""

    PREFIX = 'BK'
    LENGTH = 8  # Total length of random part

    @classmethod
    def generate(cls):
        """
        Generate a unique booking reference like BK-A3X9K2PQ.
        Uses uppercase letters and digits for readability.
        Checks DB for uniqueness before returning.
        """
        max_attempts = 10
        for _ in range(max_attempts):
            random_part = ''.join(
                random.choices(string.ascii_uppercase + string.digits, k=cls.LENGTH)
            )
            reference = f"{cls.PREFIX}-{random_part}"

            # Ensure uniqueness
            if not Booking.objects.filter(booking_reference=reference).exists():
                return reference

        raise RuntimeError("Failed to generate unique booking reference after multiple attempts.")


class BookingService:
    """
    Core booking service.

    Responsibilities:
    1. Validate and create booking within a DB transaction
    2. Update seat availability on the Show
    3. Create BookingEmailLog entry
    4. Trigger async email task via Celery
    5. Return booking instance
    """

    @classmethod
    @transaction.atomic
    def create_booking(cls, user, show_id, seats, payment_id):
        """
        Create a booking atomically.

        Uses select_for_update() to lock the Show row during seat availability
        check — prevents race conditions when multiple users book simultaneously.

        Args:
            user: Django User instance
            show_id: ID of the Show to book
            seats: List of seat numbers ["A1", "A2"]
            payment_id: Unique payment gateway reference

        Returns:
            Booking instance

        Raises:
            ValueError: If show not found, not enough seats, or duplicate payment_id
        """
        # Lock the show row to prevent concurrent overbooking
        try:
            show = Show.objects.select_for_update().get(id=show_id, is_active=True)
        except Show.DoesNotExist:
            raise ValueError(f"Show with ID {show_id} not found or inactive.")

        # Check seat availability
        seat_count = len(seats)
        if seat_count > show.available_seats:
            raise ValueError(
                f"Not enough seats available. Requested: {seat_count}, "
                f"Available: {show.available_seats}"
            )

        # Check for duplicate payment — raise distinct exception for 409 response
        if Booking.objects.filter(payment_id=payment_id).exists():
            raise DuplicatePaymentError(f"Booking with payment_id '{payment_id}' already exists.")

        # Calculate total amount
        total_amount = show.price_per_seat * seat_count

        # Generate unique booking reference
        booking_reference = BookingReferenceGenerator.generate()

        # Create the booking
        booking = Booking.objects.create(
            user=user,
            show=show,
            seats=seats,
            seat_count=seat_count,
            payment_id=payment_id,
            total_amount=total_amount,
            booking_reference=booking_reference,
            status='confirmed',
        )

        # Update available seats using F() expression — atomic DB-level decrement
        # Avoids race condition where two workers read the same value and both subtract
        Show.objects.filter(id=show.id).update(
            available_seats=F('available_seats') - seat_count
        )

        logger.info(
            f"Booking created: {booking.booking_reference} | "
            f"User: {user.email} | Show: {show.id} | Seats: {seats}"
        )

        # Create email log entry (pending state)
        email_log = BookingEmailLog.objects.create(
            booking=booking,
            recipient_email=user.email,
            status='pending',
        )

        # Trigger async email task — does NOT block the API response
        cls._trigger_confirmation_email(booking.id, email_log.id)

        return booking

    @classmethod
    def _trigger_confirmation_email(cls, booking_id, email_log_id):
        """
        Trigger the Celery task to send confirmation email.
        Import here to avoid circular imports.
        """
        try:
            from .tasks import send_booking_confirmation_email
            task = send_booking_confirmation_email.delay(booking_id, email_log_id)
            logger.info(
                f"Email task queued for booking {booking_id}. "
                f"Celery task ID: {task.id}"
            )
            # Store task ID in email log for tracking
            BookingEmailLog.objects.filter(id=email_log_id).update(
                celery_task_id=task.id
            )
        except Exception as e:
            # Email task failure should NOT fail the booking
            # Log the error and continue
            logger.error(
                f"Failed to queue email task for booking {booking_id}: {str(e)}",
                exc_info=True
            )
