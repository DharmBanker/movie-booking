"""
Bookings App — Django Admin Configuration
"""

from django.contrib import admin
from .models import Theater, Show, Booking, BookingEmailLog


@admin.register(Theater)
class TheaterAdmin(admin.ModelAdmin):
    list_display = ['name', 'city', 'state', 'total_seats', 'is_active']
    list_filter = ['city', 'state', 'is_active']
    search_fields = ['name', 'city', 'address']


@admin.register(Show)
class ShowAdmin(admin.ModelAdmin):
    list_display = ['movie', 'theater', 'show_datetime', 'language', 'format', 'available_seats', 'price_per_seat', 'is_active']
    list_filter = ['is_active', 'format', 'language', 'theater']
    search_fields = ['movie__title', 'theater__name']
    raw_id_fields = ['movie', 'theater']
    list_per_page = 50


@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = ['booking_reference', 'user', 'show', 'seat_count', 'total_amount', 'status', 'booked_at']
    list_filter = ['status', 'booked_at']
    search_fields = ['booking_reference', 'payment_id', 'user__email']
    readonly_fields = ['booking_reference', 'booked_at', 'updated_at']
    raw_id_fields = ['user', 'show']
    list_per_page = 50


@admin.register(BookingEmailLog)
class BookingEmailLogAdmin(admin.ModelAdmin):
    list_display = ['booking', 'recipient_email', 'status', 'attempts', 'last_attempt_at', 'sent_at']
    list_filter = ['status']
    search_fields = ['booking__booking_reference', 'recipient_email']
    readonly_fields = ['created_at', 'updated_at']
