"""
Bookings App — Views

Endpoints:
- POST /api/v1/bookings/              → Create a new booking
- GET  /api/v1/bookings/list/         → List all bookings
- GET  /api/v1/bookings/<ref>/        → Get booking detail by reference
- GET  /api/v1/shows/                 → List available shows
- GET  /api/v1/shows/<id>/            → Show detail

No authentication required. All bookings are created under the fixed
app user (dharm). All endpoints are fully public.
"""

import logging
from rest_framework import generics, status, serializers as drf_serializers
from rest_framework.response import Response
from rest_framework.views import APIView
from drf_spectacular.utils import extend_schema, OpenApiResponse, inline_serializer

from .models import Booking, Show
from .serializers import (
    BookingCreateSerializer,
    BookingResponseSerializer,
    BookingListSerializer,
    ShowSerializer,
)
from .services import BookingService, DuplicatePaymentError
from movies.pagination import StandardResultsPagination

logger = logging.getLogger(__name__)


class BookingCreateView(APIView):
    """
    POST /api/v1/bookings/

    Create a new booking. Triggers async email confirmation.

    Request Body:
    {
        "show": 1,
        "seats": ["A1", "A2", "A3"],
        "payment_id": "PAY_abc123xyz"
    }

    Response (201 Created):
    {
        "success": true,
        "message": "Booking confirmed! Confirmation email will be sent shortly.",
        "data": { ... }
    }
    """
    # Expose serializer to drf-spectacular for schema generation
    serializer_class = BookingCreateSerializer

    @extend_schema(
        request=BookingCreateSerializer,
        responses={
            201: BookingResponseSerializer,
            400: OpenApiResponse(description='Validation error'),
            409: OpenApiResponse(description='Duplicate payment ID'),
        }
    )
    def post(self, request, *args, **kwargs):
        serializer = BookingCreateSerializer(data=request.data)

        if not serializer.is_valid():
            return Response(
                {
                    'success': False,
                    'message': 'Invalid booking data.',
                    'errors': serializer.errors,
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        validated_data = serializer.validated_data

        # Always use the fixed app user (no auth required)
        user = _get_app_user()

        try:
            booking = BookingService.create_booking(
                user=user,
                show_id=validated_data['show'].id,
                seats=validated_data['seats'],
                payment_id=validated_data['payment_id'],
            )

            response_serializer = BookingResponseSerializer(booking)

            logger.info(
                f"Booking API: Created booking #{booking.booking_reference} "
                f"for user {user.email}"
            )

            return Response(
                {
                    'success': True,
                    'message': 'Booking confirmed! Confirmation email will be sent shortly.',
                    'data': response_serializer.data,
                },
                status=status.HTTP_201_CREATED
            )

        except DuplicatePaymentError as e:
            # 409 Conflict — payment already used for a booking
            logger.warning(f"Duplicate payment attempt: {str(e)}")
            return Response(
                {
                    'success': False,
                    'message': str(e),
                },
                status=status.HTTP_409_CONFLICT
            )

        except ValueError as e:
            logger.warning(f"Booking creation failed: {str(e)}")
            return Response(
                {
                    'success': False,
                    'message': str(e),
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        except Exception as e:
            logger.error(f"Unexpected error creating booking: {str(e)}", exc_info=True)
            return Response(
                {
                    'success': False,
                    'message': 'An unexpected error occurred. Please try again.',
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class BookingListView(generics.ListAPIView):
    """
    GET /api/v1/bookings/list/

    Returns paginated list of bookings for the authenticated user.
    """
    serializer_class = BookingListSerializer
    pagination_class = StandardResultsPagination

    def get_queryset(self):
        # Always return all bookings for the fixed app user
        return (
            Booking.objects
            .select_related('show', 'show__movie', 'show__theater')
            .order_by('-booked_at')
        )


class BookingDetailView(generics.RetrieveAPIView):
    """
    GET /api/v1/bookings/<booking_reference>/

    Returns full booking details by booking reference.
    """
    serializer_class = BookingResponseSerializer
    lookup_field = 'booking_reference'

    def get_queryset(self):
        return (
            Booking.objects
            .select_related(
                'user',
                'show',
                'show__movie',
                'show__theater',
            )
        )


class ShowListView(generics.ListAPIView):
    """
    GET /api/v1/shows/

    Returns available shows, optionally filtered by movie, theater, or date.

    Query params:
    - movie: Movie ID
    - theater: Theater ID
    - date: Show date (YYYY-MM-DD)
    """
    serializer_class = ShowSerializer
    pagination_class = StandardResultsPagination

    def get_queryset(self):
        queryset = (
            Show.objects
            .filter(is_active=True, available_seats__gt=0)
            .select_related('movie', 'theater')
            .order_by('show_datetime')
        )

        movie_id = self.request.query_params.get('movie')
        theater_id = self.request.query_params.get('theater')
        date = self.request.query_params.get('date')

        if movie_id:
            queryset = queryset.filter(movie_id=movie_id)
        if theater_id:
            queryset = queryset.filter(theater_id=theater_id)
        if date:
            queryset = queryset.filter(show_datetime__date=date)

        return queryset


class ShowDetailView(generics.RetrieveAPIView):
    """
    GET /api/v1/shows/<id>/

    Returns full show details.
    """
    serializer_class = ShowSerializer
    queryset = Show.objects.filter(is_active=True).select_related('movie', 'theater')


class ShowBookedSeatsView(generics.RetrieveAPIView):
    """
    GET /api/v1/shows/<id>/booked-seats/

    Returns list of already-booked seat numbers for a show.
    Used by the frontend seat map to mark unavailable seats.
    """
    queryset = Show.objects.filter(is_active=True)

    # Use ShowSerializer as the declared serializer_class so drf-spectacular
    # can introspect the view. The actual response is built manually below.
    serializer_class = ShowSerializer

    @extend_schema(
        responses={
            200: inline_serializer(
                name='BookedSeatsResponse',
                fields={
                    'show_id':         drf_serializers.IntegerField(),
                    'total_seats':     drf_serializers.IntegerField(),
                    'available_seats': drf_serializers.IntegerField(),
                    'booked_seats':    drf_serializers.ListField(child=drf_serializers.CharField()),
                }
            )
        }
    )
    def retrieve(self, request, *args, **kwargs):
        show = self.get_object()
        booked = Booking.objects.filter(
            show=show,
            status__in=['confirmed', 'pending']
        ).values_list('seats', flat=True)

        booked_seats = []
        for seat_list in booked:
            booked_seats.extend(seat_list)

        return Response({
            'show_id':         show.id,
            'total_seats':     show.total_seats,
            'available_seats': show.available_seats,
            'booked_seats':    sorted(set(booked_seats)),
        })


def _get_app_user():
    """
    Returns the fixed application user (dharm).
    All bookings are created under this user — no authentication required.
    Created automatically by the create_app_user management command at deploy time.
    """
    from django.contrib.auth.models import User
    user, _ = User.objects.get_or_create(
        username='dharm',
        defaults={
            'email': 'dharm@moviebooking.com',
            'first_name': 'Dharm',
            'last_name': '',
            'is_staff': True,
            'is_superuser': True,
        }
    )
    return user
