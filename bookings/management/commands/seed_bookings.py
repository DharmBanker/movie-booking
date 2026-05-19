"""
Management Command: seed_bookings

Seeds the database with sample theaters, shows, and a demo user for testing.

Usage:
    python manage.py seed_bookings
"""

import random
from datetime import datetime, timedelta
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.utils import timezone
from movies.models import Movie
from bookings.models import Theater, Show


THEATERS = [
    {
        'name': 'PVR Cinemas — Phoenix Mall',
        'address': 'Phoenix Marketcity, Nagar Road',
        'city': 'Pune',
        'state': 'Maharashtra',
        'pincode': '411014',
        'total_seats': 250,
    },
    {
        'name': 'INOX — Insignia',
        'address': 'Bund Garden Road, Sangamvadi',
        'city': 'Pune',
        'state': 'Maharashtra',
        'pincode': '411001',
        'total_seats': 200,
    },
    {
        'name': 'Cinepolis — Fun Republic',
        'address': 'Fun Republic Mall, Andheri West',
        'city': 'Mumbai',
        'state': 'Maharashtra',
        'pincode': '400053',
        'total_seats': 300,
    },
    {
        'name': 'PVR — Select Citywalk',
        'address': 'Select Citywalk Mall, Saket',
        'city': 'Delhi',
        'state': 'Delhi',
        'pincode': '110017',
        'total_seats': 280,
    },
    {
        'name': 'INOX — Garuda Mall',
        'address': 'Garuda Mall, Magrath Road',
        'city': 'Bangalore',
        'state': 'Karnataka',
        'pincode': '560025',
        'total_seats': 220,
    },
]


class Command(BaseCommand):
    help = 'Seed the database with sample theaters, shows, and demo user'

    def handle(self, *args, **options):
        # Create demo user
        self.stdout.write('Creating demo user...')
        demo_user, created = User.objects.get_or_create(
            username='demo_user',
            defaults={
                'email': 'demo@moviebooking.com',
                'first_name': 'Demo',
                'last_name': 'User',
            }
        )
        if created:
            demo_user.set_password('demo123456')
            demo_user.save()
            self.stdout.write(f'  Created user: {demo_user.email}')
        else:
            self.stdout.write(f'  User already exists: {demo_user.email}')

        # Create theaters
        self.stdout.write('Creating theaters...')
        theater_objects = []
        for theater_data in THEATERS:
            theater, created = Theater.objects.get_or_create(
                name=theater_data['name'],
                defaults={**theater_data, 'is_active': True}
            )
            theater_objects.append(theater)
            if created:
                self.stdout.write(f'  Created theater: {theater.name}')

        # Create shows for existing movies
        self.stdout.write('Creating shows...')
        movies = list(Movie.objects.filter(is_active=True)[:10])

        if not movies:
            self.stdout.write(self.style.WARNING(
                'No movies found. Run "python manage.py seed_movies" first.'
            ))
            return

        show_times = ['10:00', '13:30', '16:00', '19:00', '22:00']
        languages = ['Hindi', 'English', 'Tamil', 'Telugu']
        formats = ['2D', '3D', 'IMAX']
        prices = [150, 200, 250, 300, 350, 400]

        shows_created = 0
        today = timezone.now().date()

        for movie in movies:
            for theater in random.sample(theater_objects, min(3, len(theater_objects))):
                for days_ahead in range(0, 7):  # Shows for next 7 days
                    show_date = today + timedelta(days=days_ahead)
                    for time_str in random.sample(show_times, 2):  # 2 shows per day
                        hour, minute = map(int, time_str.split(':'))
                        show_datetime = timezone.make_aware(
                            datetime(show_date.year, show_date.month, show_date.day, hour, minute)
                        )

                        show, created = Show.objects.get_or_create(
                            movie=movie,
                            theater=theater,
                            show_datetime=show_datetime,
                            defaults={
                                'language': random.choice(languages),
                                'format': random.choice(formats),
                                'total_seats': theater.total_seats,
                                'available_seats': theater.total_seats,
                                'price_per_seat': random.choice(prices),
                                'is_active': True,
                            }
                        )
                        if created:
                            shows_created += 1

        self.stdout.write(self.style.SUCCESS(
            f'\n✓ Seeding complete!\n'
            f'  Theaters: {Theater.objects.count()}\n'
            f'  Shows created: {shows_created}\n'
            f'  Total shows: {Show.objects.count()}\n'
            f'\nDemo user credentials:\n'
            f'  Email: demo@moviebooking.com\n'
            f'  Password: demo123456\n'
        ))
