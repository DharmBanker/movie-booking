"""
Bookings App — Database Models

Schema:
- Theater: Physical cinema location
- Show: A specific screening of a movie at a theater
- Seat: Individual seats in a show
- Booking: A user's ticket booking (links User, Show, Seats)
- BookingEmailLog: Tracks email sending status for monitoring

Design decisions:
- Booking uses payment_id for idempotency (prevents duplicate bookings)
- Seats are stored as JSON array for flexibility
- BookingEmailLog enables retry logic and monitoring
"""

from django.db import models
from django.contrib.auth.models import User
from movies.models import Movie


class Theater(models.Model):
    """
    Physical cinema/theater location.
    """
    name = models.CharField(max_length=255)
    address = models.TextField()
    city = models.CharField(max_length=100, db_index=True)
    state = models.CharField(max_length=100)
    pincode = models.CharField(max_length=10)
    total_seats = models.PositiveIntegerField(default=200)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'theaters'
        ordering = ['name']
        indexes = [
            models.Index(fields=['city'], name='idx_theater_city'),
            models.Index(fields=['is_active'], name='idx_theater_active'),
        ]

    def __str__(self):
        return f"{self.name} — {self.city}"


class Show(models.Model):
    """
    A specific screening of a movie at a theater on a given date/time.

    Relationships:
    - movie: FK to Movie
    - theater: FK to Theater
    """
    movie = models.ForeignKey(
        Movie,
        on_delete=models.CASCADE,
        related_name='shows'
    )
    theater = models.ForeignKey(
        Theater,
        on_delete=models.CASCADE,
        related_name='shows'
    )
    show_datetime = models.DateTimeField(db_index=True)
    language = models.CharField(max_length=100)  # Language of this specific show
    format = models.CharField(
        max_length=20,
        choices=[('2D', '2D'), ('3D', '3D'), ('IMAX', 'IMAX'), ('4DX', '4DX')],
        default='2D'
    )
    total_seats = models.PositiveIntegerField(default=200)
    available_seats = models.PositiveIntegerField(default=200)
    price_per_seat = models.DecimalField(max_digits=8, decimal_places=2)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'shows'
        ordering = ['show_datetime']
        indexes = [
            models.Index(fields=['show_datetime'], name='idx_show_datetime'),
            models.Index(fields=['movie', 'show_datetime'], name='idx_show_movie_datetime'),
            models.Index(fields=['theater', 'show_datetime'], name='idx_show_theater_datetime'),
            models.Index(fields=['is_active'], name='idx_show_active'),
        ]

    def __str__(self):
        return f"{self.movie.title} @ {self.theater.name} — {self.show_datetime}"


class Booking(models.Model):
    """
    A user's ticket booking.

    Stores:
    - Which user booked
    - Which show
    - Which seats (JSON array)
    - Payment reference
    - Booking status

    payment_id is unique to prevent duplicate bookings from payment retries.
    """

    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('confirmed', 'Confirmed'),
        ('cancelled', 'Cancelled'),
        ('refunded', 'Refunded'),
    ]

    # Core relationships
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='bookings'
    )
    show = models.ForeignKey(
        Show,
        on_delete=models.CASCADE,
        related_name='bookings'
    )

    # Seat information stored as JSON array
    # Example: ["A1", "A2", "A3"]
    seats = models.JSONField(
        default=list,
        help_text="List of seat numbers booked"
    )
    seat_count = models.PositiveIntegerField(default=1)

    # Payment
    payment_id = models.CharField(
        max_length=255,
        unique=True,  # Prevents duplicate bookings
        db_index=True
    )
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)

    # Status
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='confirmed',
        db_index=True
    )

    # Booking reference (user-facing ID)
    booking_reference = models.CharField(
        max_length=20,
        unique=True,
        db_index=True
    )

    # Timestamps
    booked_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'bookings'
        ordering = ['-booked_at']
        indexes = [
            models.Index(fields=['user', '-booked_at'], name='idx_booking_user_date'),
            models.Index(fields=['status'], name='idx_booking_status'),
            models.Index(fields=['payment_id'], name='idx_booking_payment'),
            models.Index(fields=['booking_reference'], name='idx_booking_reference'),
        ]

    def __str__(self):
        return f"Booking #{self.booking_reference} — {self.user.email}"

    @property
    def seats_display(self):
        """Return seats as comma-separated string for display."""
        return ', '.join(self.seats) if self.seats else 'N/A'


class BookingEmailLog(models.Model):
    """
    Tracks email sending status for each booking.

    Used for:
    - Monitoring email delivery
    - Retry logic (track failed attempts)
    - Debugging email issues

    This is separate from Booking to keep concerns separated.
    """

    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('sent', 'Sent'),
        ('failed', 'Failed'),
        ('retrying', 'Retrying'),
    ]

    booking = models.OneToOneField(
        Booking,
        on_delete=models.CASCADE,
        related_name='email_log'
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending',
        db_index=True
    )
    recipient_email = models.EmailField()
    attempts = models.PositiveIntegerField(default=0)
    last_attempt_at = models.DateTimeField(null=True, blank=True)
    sent_at = models.DateTimeField(null=True, blank=True)
    error_message = models.TextField(blank=True)
    celery_task_id = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'booking_email_logs'
        indexes = [
            models.Index(fields=['status'], name='idx_email_log_status'),
            models.Index(fields=['booking'], name='idx_email_log_booking'),
        ]

    def __str__(self):
        return f"EmailLog for Booking #{self.booking.booking_reference} — {self.status}"
