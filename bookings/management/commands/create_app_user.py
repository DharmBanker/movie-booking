"""
Management Command: create_app_user

Creates the fixed application user (dharm / dharm1234) used for all bookings.
Also grants superuser access so the admin panel is accessible.

Run automatically during Vercel build via build_files.sh.
Safe to run multiple times — uses get_or_create, only updates password if user exists.

Usage:
    python manage.py create_app_user
"""

from django.core.management.base import BaseCommand
from django.contrib.auth.models import User


class Command(BaseCommand):
    help = 'Create the fixed application user (dharm) for bookings and admin access.'

    def handle(self, *args, **options):
        username = 'dharm'
        password = 'dharm1234'
        email = 'dharm@moviebooking.com'

        user, created = User.objects.get_or_create(
            username=username,
            defaults={
                'email': email,
                'first_name': 'Dharm',
                'last_name': '',
                'is_staff': True,
                'is_superuser': True,
                'is_active': True,
            }
        )

        # Always set the password (handles re-deploys where user already exists)
        user.set_password(password)

        # Ensure staff/superuser flags are set even if user pre-existed
        user.is_staff = True
        user.is_superuser = True
        user.is_active = True
        user.save()

        if created:
            self.stdout.write(
                self.style.SUCCESS(
                    f'✓ App user created: username="{username}" password="{password}"'
                )
            )
        else:
            self.stdout.write(
                self.style.SUCCESS(
                    f'✓ App user already exists — password reset to "{password}"'
                )
            )
