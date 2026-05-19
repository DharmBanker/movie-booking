#!/bin/bash
# =============================================================
# Vercel Build Script
# Runs during Vercel deployment build phase
# =============================================================

set -e  # Exit immediately on any error

echo "=== Installing dependencies ==="
pip install -r requirements.txt

echo "=== Running database migrations ==="
python manage.py migrate --noinput

echo "=== Creating app user (dharm) ==="
python manage.py create_app_user

echo "=== Collecting static files ==="
python manage.py collectstatic --noinput

echo "=== Build complete ==="
