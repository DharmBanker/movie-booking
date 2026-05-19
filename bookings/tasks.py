"""
Bookings App — Celery Tasks

Background tasks for async email processing.

Task: send_booking_confirmation_email
- Sends HTML confirmation email after booking
- Implements retry logic with exponential backoff
- Logs all attempts (success, failure, retry)
- Never blocks the booking API response
"""

import logging
from datetime import datetime

from celery import shared_task
from celery.exceptions import MaxRetriesExceededError
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils import timezone
from django.conf import settings

logger = logging.getLogger(__name__)


@shared_task(
    bind=True,
    max_retries=3,           # Retry up to 3 times on failure
    default_retry_delay=60,  # Base delay: 60 seconds
    name='bookings.send_booking_confirmation_email',
    # Ensure task result is tracked
    track_started=True,
)
def send_booking_confirmation_email(self, booking_id, email_log_id):
    """
    Celery task: Send booking confirmation email asynchronously.

    Flow:
    1. Load booking and email log from DB
    2. Render HTML email template
    3. Send email via configured SMTP backend
    4. Update email log status to 'sent'
    5. On failure: retry with exponential backoff (60s, 120s, 240s)
    6. After max retries: mark as 'failed' and log error

    Args:
        booking_id: ID of the Booking to send email for
        email_log_id: ID of the BookingEmailLog to update

    Retry Strategy:
        Attempt 1: Immediate
        Attempt 2: 60 seconds later
        Attempt 3: 120 seconds later (60 * 2^1)
        Attempt 4: 240 seconds later (60 * 2^2)
        After 4 attempts: Mark as failed
    """
    from .models import Booking, BookingEmailLog

    logger.info(f"[EMAIL TASK] Starting email task for booking_id={booking_id}")

    # Load email log for status tracking
    try:
        email_log = BookingEmailLog.objects.select_related('booking').get(id=email_log_id)
    except BookingEmailLog.DoesNotExist:
        logger.error(f"[EMAIL TASK] EmailLog {email_log_id} not found. Aborting.")
        return

    # Update log: mark as retrying if this is a retry attempt
    attempt_number = self.request.retries + 1
    email_log.attempts = attempt_number
    email_log.last_attempt_at = timezone.now()
    email_log.status = 'retrying' if self.request.retries > 0 else 'pending'
    email_log.save(update_fields=['attempts', 'last_attempt_at', 'status'])

    logger.info(
        f"[EMAIL TASK] Attempt {attempt_number}/4 for booking_id={booking_id}"
    )

    # Load booking with all related data needed for email
    try:
        booking = (
            Booking.objects
            .select_related(
                'user',
                'show',
                'show__movie',
                'show__theater',
            )
            .get(id=booking_id)
        )
    except Booking.DoesNotExist:
        logger.error(f"[EMAIL TASK] Booking {booking_id} not found. Aborting.")
        email_log.status = 'failed'
        email_log.error_message = f"Booking {booking_id} not found in database."
        email_log.save(update_fields=['status', 'error_message'])
        return

    try:
        # Build email context for template rendering
        context = _build_email_context(booking)

        # Render HTML and plain text versions
        html_content = render_to_string(
            'emails/booking_confirmation.html',
            context
        )
        text_content = render_to_string(
            'emails/booking_confirmation.txt',
            context
        )

        # Build email message
        subject = f"Booking Confirmed! #{booking.booking_reference} — {booking.show.movie.title}"
        from_email = settings.DEFAULT_FROM_EMAIL
        to_email = [booking.user.email]

        # EmailMultiAlternatives sends both HTML and plain text
        # Email clients that don't support HTML will show plain text
        email = EmailMultiAlternatives(
            subject=subject,
            body=text_content,
            from_email=from_email,
            to=to_email,
        )
        email.attach_alternative(html_content, "text/html")

        # Send the email
        email.send(fail_silently=False)

        # Update email log: success
        email_log.status = 'sent'
        email_log.sent_at = timezone.now()
        email_log.error_message = ''
        email_log.save(update_fields=['status', 'sent_at', 'error_message'])

        logger.info(
            f"[EMAIL TASK] ✓ Email sent successfully for booking "
            f"#{booking.booking_reference} to {booking.user.email}"
        )

    except Exception as exc:
        # Log the failure
        error_msg = str(exc)
        logger.warning(
            f"[EMAIL TASK] ✗ Attempt {attempt_number} failed for booking "
            f"#{booking_id}: {error_msg}"
        )

        # Update log with error
        email_log.error_message = error_msg
        email_log.save(update_fields=['error_message'])

        try:
            # Exponential backoff: delay doubles with each retry
            # Retry 1: 60s, Retry 2: 120s, Retry 3: 240s
            retry_delay = 60 * (2 ** self.request.retries)

            logger.info(
                f"[EMAIL TASK] Scheduling retry in {retry_delay}s "
                f"(attempt {attempt_number + 1}/4)"
            )

            raise self.retry(exc=exc, countdown=retry_delay)

        except MaxRetriesExceededError:
            # All retries exhausted — mark as permanently failed
            email_log.status = 'failed'
            email_log.save(update_fields=['status'])

            logger.error(
                f"[EMAIL TASK] ✗✗ All retries exhausted for booking "
                f"#{booking_id}. Email permanently failed. "
                f"Last error: {error_msg}",
                exc_info=True
            )


def _build_email_context(booking):
    """
    Build the template context dictionary for the confirmation email.

    Args:
        booking: Booking instance with related show, movie, theater, user loaded

    Returns:
        dict: Context for email template rendering
    """
    show = booking.show
    movie = show.movie
    theater = show.theater

    return {
        # Booking details
        'booking_reference': booking.booking_reference,
        'booking_status': booking.get_status_display(),
        'booked_at': booking.booked_at,

        # User details
        'user_name': booking.user.get_full_name() or booking.user.username,
        'user_email': booking.user.email,

        # Movie details
        'movie_title': movie.title,
        'movie_poster_url': movie.poster_url,
        'movie_duration': movie.duration_minutes,
        'movie_certificate': movie.certificate,

        # Show details
        'show_datetime': show.show_datetime,
        'show_language': show.language,
        'show_format': show.format,

        # Theater details
        'theater_name': theater.name,
        'theater_address': theater.address,
        'theater_city': theater.city,

        # Seat details
        'seats': booking.seats,
        'seats_display': booking.seats_display,
        'seat_count': booking.seat_count,

        # Payment details
        'payment_id': booking.payment_id,
        'total_amount': booking.total_amount,
        'price_per_seat': show.price_per_seat,

        # App settings
        'frontend_url': settings.FRONTEND_URL,
        'support_email': settings.DEFAULT_FROM_EMAIL,
        'current_year': datetime.now().year,
    }
