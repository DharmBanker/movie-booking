web: gunicorn movie_booking.wsgi:application --bind 0.0.0.0:$PORT --workers 4 --timeout 120
worker: celery -A movie_booking worker --loglevel=info --concurrency=4
