"""
Bookings App — Serializers

Serializers for:
- BookingCreateSerializer: Validates and creates a booking
- BookingResponseSerializer: Returns booking confirmation data
- ShowSerializer: Show details for booking context
- TheaterSerializer: Theater details
"""

from datetime import datetime
from rest_framework import serializers
from drf_spectacular.utils import extend_schema_field
from .models import Booking, Show, Theater
from movies.serializers import MovieListSerializer


class TheaterSerializer(serializers.ModelSerializer):
    """Minimal theater data for booking responses."""

    class Meta:
        model = Theater
        fields = ['id', 'name', 'address', 'city', 'state']


class ShowSerializer(serializers.ModelSerializer):
    """Show details including movie and theater info."""
    movie = MovieListSerializer(read_only=True)
    theater = TheaterSerializer(read_only=True)

    class Meta:
        model = Show
        fields = [
            'id',
            'movie',
            'theater',
            'show_datetime',
            'language',
            'format',
            'price_per_seat',
            'available_seats',
        ]


class BookingCreateSerializer(serializers.ModelSerializer):
    """
    Validates booking creation request.

    Required fields:
    - show: Show ID
    - seats: List of seat numbers (e.g., ["A1", "A2"])
    - payment_id: Unique payment reference from payment gateway

    Note: payment_id uniqueness is NOT validated here — it is checked in
    BookingService.create_booking() which raises DuplicatePaymentError (→ 409).
    Doing it here would return 400 instead of the correct 409 Conflict.
    """
    seats = serializers.ListField(
        child=serializers.CharField(max_length=10),
        min_length=1,
        help_text='List of seat numbers to book, e.g. ["A1", "A2"]'
    )
    # payment_id declared explicitly so we can skip the unique validator
    payment_id = serializers.CharField(
        max_length=255,
        validators=[],  # uniqueness enforced in service layer → returns 409
    )

    class Meta:
        model = Booking
        fields = ['show', 'seats', 'payment_id']

    def validate_seats(self, value):
        """Validate seat count doesn't exceed maximum allowed."""
        from django.conf import settings
        max_seats = getattr(settings, 'MAX_SEATS_PER_BOOKING', 10)

        if len(value) > max_seats:
            raise serializers.ValidationError(
                f"Cannot book more than {max_seats} seats at once."
            )

        # Remove duplicates while preserving order
        seen = set()
        unique_seats = []
        for seat in value:
            if seat not in seen:
                seen.add(seat)
                unique_seats.append(seat)

        return unique_seats

    def validate(self, attrs):
        """Cross-field validation: check show is active and has enough seats."""
        show = attrs.get('show')
        seats = attrs.get('seats', [])

        if show and not show.is_active:
            raise serializers.ValidationError({"show": "This show is no longer available."})

        if show and len(seats) > show.available_seats:
            raise serializers.ValidationError({
                "seats": f"Only {show.available_seats} seats available for this show."
            })

        return attrs


class BookingResponseSerializer(serializers.ModelSerializer):
    """
    Full booking confirmation response.
    Returned after successful booking creation.
    """
    show = ShowSerializer(read_only=True)
    user_email = serializers.SerializerMethodField()
    seats_display = serializers.SerializerMethodField()

    class Meta:
        model = Booking
        fields = [
            'id',
            'booking_reference',
            'user_email',
            'show',
            'seats',
            'seats_display',
            'seat_count',
            'payment_id',
            'total_amount',
            'status',
            'booked_at',
        ]

    @extend_schema_field(serializers.EmailField())
    def get_user_email(self, obj) -> str:
        return obj.user.email

    @extend_schema_field(serializers.CharField())
    def get_seats_display(self, obj) -> str:
        return ', '.join(obj.seats) if obj.seats else 'N/A'


class BookingListSerializer(serializers.ModelSerializer):
    """Compact serializer for booking list views."""
    movie_title = serializers.SerializerMethodField()
    theater_name = serializers.SerializerMethodField()
    show_datetime = serializers.SerializerMethodField()

    class Meta:
        model = Booking
        fields = [
            'id',
            'booking_reference',
            'movie_title',
            'theater_name',
            'show_datetime',
            'seats',
            'seat_count',
            'total_amount',
            'status',
            'booked_at',
        ]

    @extend_schema_field(serializers.CharField())
    def get_movie_title(self, obj) -> str:
        return obj.show.movie.title

    @extend_schema_field(serializers.CharField())
    def get_theater_name(self, obj) -> str:
        return obj.show.theater.name

    @extend_schema_field(serializers.DateTimeField())
    def get_show_datetime(self, obj) -> datetime:
        return obj.show.show_datetime
