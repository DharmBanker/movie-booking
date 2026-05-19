"""
Bookings App — URL Configuration
"""

from django.urls import path
from . import views

app_name = 'bookings'

urlpatterns = [
    # Booking endpoints
    path('bookings/', views.BookingCreateView.as_view(), name='booking-create'),
    path('bookings/list/', views.BookingListView.as_view(), name='booking-list'),
    path('bookings/<str:booking_reference>/', views.BookingDetailView.as_view(), name='booking-detail'),

    # Show endpoints
    path('shows/', views.ShowListView.as_view(), name='show-list'),
    path('shows/<int:pk>/', views.ShowDetailView.as_view(), name='show-detail'),
    path('shows/<int:pk>/booked-seats/', views.ShowBookedSeatsView.as_view(), name='show-booked-seats'),
]
