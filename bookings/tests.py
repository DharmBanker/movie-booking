"""
Bookings App — Tests

Covers:
- Theater model
- Show model
- Booking model
- BookingService: create_booking, duplicate payment, seat overflow
- BookingCreateView: POST /api/v1/bookings/
- BookingDetailView: GET /api/v1/bookings/<ref>/
- BookingListView: GET /api/v1/bookings/list/
- ShowListView: GET /api/v1/shows/
- DuplicatePaymentError returns 409
"""

from decimal import Decimal
from django.test import TestCase
from django.contrib.auth.models import User
from django.urls import reverse
from django.utils import timezone
from rest_framework.test import APITestCase
from rest_framework import status

from movies.models import Movie, Genre, Language
from .models import Theater, Show, Booking, BookingEmailLog
from .services import BookingService, DuplicatePaymentError


# ============================================================
# Helpers
# ============================================================

def make_movie(title='Test Movie', slug='test-movie'):
    return Movie.objects.create(
        title=title, slug=slug, description='desc',
        duration_minutes=120, release_date='2024-01-01',
        status='now_showing', is_active=True,
    )


def make_theater(name='PVR Test', city='Mumbai'):
    return Theater.objects.create(
        name=name, address='123 Main St', city=city,
        state='Maharashtra', pincode='400001', total_seats=200,
    )


def make_show(movie, theater, price=200, available=200):
    return Show.objects.create(
        movie=movie,
        theater=theater,
        show_datetime=timezone.now() + timezone.timedelta(days=1),
        language='Hindi',
        format='2D',
        total_seats=available,
        available_seats=available,
        price_per_seat=Decimal(str(price)),
        is_active=True,
    )


def make_user(username='testuser', email='test@example.com'):
    user, _ = User.objects.get_or_create(
        username=username,
        defaults={'email': email, 'first_name': 'Test', 'last_name': 'User'},
    )
    return user


# ============================================================
# Model Tests
# ============================================================

class TheaterModelTest(TestCase):
    def test_create_theater(self):
        t = make_theater()
        self.assertEqual(str(t), 'PVR Test — Mumbai')
        self.assertTrue(t.is_active)


class ShowModelTest(TestCase):
    def test_create_show(self):
        movie = make_movie()
        theater = make_theater()
        show = make_show(movie, theater)
        self.assertIn(movie.title, str(show))
        self.assertIn(theater.name, str(show))
        self.assertEqual(show.available_seats, 200)


class BookingModelTest(TestCase):
    def test_seats_display(self):
        user = make_user()
        movie = make_movie()
        theater = make_theater()
        show = make_show(movie, theater)
        booking = Booking.objects.create(
            user=user, show=show,
            seats=['A1', 'A2', 'B3'],
            seat_count=3,
            payment_id='PAY_TEST_MODEL',
            total_amount=Decimal('600.00'),
            booking_reference='BK-TESTREF1',
            status='confirmed',
        )
        self.assertEqual(booking.seats_display, 'A1, A2, B3')
        self.assertIn('BK-TESTREF1', str(booking))

    def test_seats_display_empty(self):
        user = make_user()
        movie = make_movie()
        theater = make_theater()
        show = make_show(movie, theater)
        booking = Booking.objects.create(
            user=user, show=show,
            seats=[],
            seat_count=0,
            payment_id='PAY_EMPTY',
            total_amount=Decimal('0.00'),
            booking_reference='BK-EMPTY001',
            status='confirmed',
        )
        self.assertEqual(booking.seats_display, 'N/A')


# ============================================================
# Service Tests
# ============================================================

class BookingServiceTest(TestCase):
    def setUp(self):
        self.user = make_user()
        self.movie = make_movie()
        self.theater = make_theater()
        self.show = make_show(self.movie, self.theater, price=250, available=50)

    def test_create_booking_success(self):
        booking = BookingService.create_booking(
            user=self.user,
            show_id=self.show.id,
            seats=['A1', 'A2'],
            payment_id='PAY_SVC_001',
        )
        self.assertEqual(booking.seat_count, 2)
        self.assertEqual(booking.total_amount, Decimal('500.00'))
        self.assertEqual(booking.status, 'confirmed')
        self.assertTrue(booking.booking_reference.startswith('BK-'))

    def test_create_booking_decrements_available_seats(self):
        BookingService.create_booking(
            user=self.user,
            show_id=self.show.id,
            seats=['C1', 'C2', 'C3'],
            payment_id='PAY_SVC_002',
        )
        self.show.refresh_from_db()
        self.assertEqual(self.show.available_seats, 47)

    def test_create_booking_creates_email_log(self):
        booking = BookingService.create_booking(
            user=self.user,
            show_id=self.show.id,
            seats=['D1'],
            payment_id='PAY_SVC_003',
        )
        self.assertTrue(BookingEmailLog.objects.filter(booking=booking).exists())
        log = BookingEmailLog.objects.get(booking=booking)
        self.assertEqual(log.recipient_email, self.user.email)

    def test_duplicate_payment_raises_error(self):
        BookingService.create_booking(
            user=self.user,
            show_id=self.show.id,
            seats=['E1'],
            payment_id='PAY_DUP_001',
        )
        with self.assertRaises(DuplicatePaymentError):
            BookingService.create_booking(
                user=self.user,
                show_id=self.show.id,
                seats=['E2'],
                payment_id='PAY_DUP_001',  # same payment_id
            )

    def test_insufficient_seats_raises_value_error(self):
        show = make_show(self.movie, self.theater, available=2)
        with self.assertRaises(ValueError) as ctx:
            BookingService.create_booking(
                user=self.user,
                show_id=show.id,
                seats=['F1', 'F2', 'F3'],  # 3 seats, only 2 available
                payment_id='PAY_OVERFLOW',
            )
        self.assertIn('Not enough seats', str(ctx.exception))

    def test_inactive_show_raises_value_error(self):
        self.show.is_active = False
        self.show.save()
        with self.assertRaises(ValueError) as ctx:
            BookingService.create_booking(
                user=self.user,
                show_id=self.show.id,
                seats=['G1'],
                payment_id='PAY_INACTIVE',
            )
        self.assertIn('not found or inactive', str(ctx.exception))

    def test_nonexistent_show_raises_value_error(self):
        with self.assertRaises(ValueError):
            BookingService.create_booking(
                user=self.user,
                show_id=99999,
                seats=['H1'],
                payment_id='PAY_NOSHOW',
            )


# ============================================================
# API Tests — Booking Create
# ============================================================

class BookingCreateAPITest(APITestCase):
    def setUp(self):
        self.user = make_user()
        self.movie = make_movie()
        self.theater = make_theater()
        self.show = make_show(self.movie, self.theater, price=300, available=100)
        self.url = reverse('bookings:booking-create')

    def test_create_booking_returns_201(self):
        response = self.client.post(self.url, {
            'show': self.show.id,
            'seats': ['A1', 'A2'],
            'payment_id': 'PAY_API_001',
        }, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(response.data['success'])
        self.assertIn('booking_reference', response.data['data'])

    def test_create_booking_response_has_all_fields(self):
        response = self.client.post(self.url, {
            'show': self.show.id,
            'seats': ['B1'],
            'payment_id': 'PAY_API_002',
        }, format='json')
        data = response.data['data']
        self.assertIn('booking_reference', data)
        self.assertIn('seats', data)
        self.assertIn('seat_count', data)
        self.assertIn('total_amount', data)
        self.assertIn('status', data)
        self.assertIn('show', data)
        self.assertEqual(data['status'], 'confirmed')

    def test_duplicate_payment_returns_409(self):
        self.client.post(self.url, {
            'show': self.show.id,
            'seats': ['C1'],
            'payment_id': 'PAY_DUP_API',
        }, format='json')
        response = self.client.post(self.url, {
            'show': self.show.id,
            'seats': ['C2'],
            'payment_id': 'PAY_DUP_API',
        }, format='json')
        self.assertEqual(response.status_code, status.HTTP_409_CONFLICT)
        self.assertFalse(response.data['success'])

    def test_missing_fields_returns_400(self):
        response = self.client.post(self.url, {
            'show': self.show.id,
            # missing seats and payment_id
        }, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(response.data['success'])
        self.assertIn('errors', response.data)

    def test_empty_seats_returns_400(self):
        response = self.client.post(self.url, {
            'show': self.show.id,
            'seats': [],
            'payment_id': 'PAY_EMPTY_SEATS',
        }, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_too_many_seats_returns_400(self):
        seats = [f'Z{i}' for i in range(11)]  # 11 seats, max is 10
        response = self.client.post(self.url, {
            'show': self.show.id,
            'seats': seats,
            'payment_id': 'PAY_TOO_MANY',
        }, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_total_amount_calculated_correctly(self):
        response = self.client.post(self.url, {
            'show': self.show.id,
            'seats': ['D1', 'D2', 'D3'],
            'payment_id': 'PAY_AMOUNT_CHECK',
        }, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        # 3 seats × ₹300 = ₹900
        self.assertEqual(response.data['data']['total_amount'], '900.00')

    def test_duplicate_seats_deduplicated(self):
        response = self.client.post(self.url, {
            'show': self.show.id,
            'seats': ['E1', 'E1', 'E2'],  # E1 duplicated
            'payment_id': 'PAY_DEDUP',
        }, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['data']['seat_count'], 2)


# ============================================================
# API Tests — Booking Detail
# ============================================================

class BookingDetailAPITest(APITestCase):
    def setUp(self):
        self.user = make_user()
        self.movie = make_movie()
        self.theater = make_theater()
        self.show = make_show(self.movie, self.theater)
        self.booking = Booking.objects.create(
            user=self.user, show=self.show,
            seats=['A1', 'A2'],
            seat_count=2,
            payment_id='PAY_DETAIL_001',
            total_amount=Decimal('400.00'),
            booking_reference='BK-DETAIL01',
            status='confirmed',
        )

    def test_get_booking_by_reference(self):
        url = reverse('bookings:booking-detail', kwargs={'booking_reference': 'BK-DETAIL01'})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['booking_reference'], 'BK-DETAIL01')
        self.assertEqual(response.data['seats'], ['A1', 'A2'])

    def test_booking_detail_includes_show_info(self):
        url = reverse('bookings:booking-detail', kwargs={'booking_reference': 'BK-DETAIL01'})
        response = self.client.get(url)
        self.assertIn('show', response.data)
        self.assertIn('movie', response.data['show'])
        self.assertIn('theater', response.data['show'])

    def test_booking_detail_404_for_unknown_reference(self):
        url = reverse('bookings:booking-detail', kwargs={'booking_reference': 'BK-NOTEXIST'})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


# ============================================================
# API Tests — Show List
# ============================================================

class ShowListAPITest(APITestCase):
    def setUp(self):
        self.movie = make_movie()
        self.theater = make_theater()
        self.show = make_show(self.movie, self.theater)
        self.url = reverse('bookings:show-list')

    def test_show_list_returns_200(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(response.data['count'], 1)

    def test_show_list_filter_by_movie(self):
        response = self.client.get(self.url, {'movie': self.movie.id})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        for show in response.data['results']:
            self.assertEqual(show['movie']['id'], self.movie.id)

    def test_show_list_excludes_inactive(self):
        inactive_show = make_show(self.movie, self.theater)
        inactive_show.is_active = False
        inactive_show.save()
        response = self.client.get(self.url)
        show_ids = [s['id'] for s in response.data['results']]
        self.assertNotIn(inactive_show.id, show_ids)

    def test_show_list_excludes_sold_out(self):
        sold_out = make_show(self.movie, self.theater, available=0)
        response = self.client.get(self.url)
        show_ids = [s['id'] for s in response.data['results']]
        self.assertNotIn(sold_out.id, show_ids)
