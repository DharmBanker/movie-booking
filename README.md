# Movie Booking Backend

A scalable movie booking system built with Django, Django REST Framework, Celery, Redis, and PostgreSQL.

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend | Django 4.2, Django REST Framework |
| Database | PostgreSQL (SQLite for local dev) |
| Background Tasks | Celery + Redis |
| Email | Django SMTP / Console backend |
| API Docs | drf-spectacular (Swagger + ReDoc) |
| Production Server | Gunicorn + Whitenoise |

---

## Features

### Task 1 — Scalable Genre & Language Filtering
- Multi-select genre filtering (`?genres=1,2,3`)
- Multi-select language filtering (`?languages=1,2`)
- Sorting by rating, release date, title
- Full-text search by title/director
- Pagination with configurable page size
- **Dynamic filter counts** — counts update based on current selection
- 15+ database indexes for query performance at 5000+ records
- `prefetch_related` on M2M relations — zero N+1 queries

### Task 2 — Automated Booking Email Confirmation
- Atomic booking creation with `select_for_update()` — prevents overbooking
- Async email via Celery — API responds instantly, email sends in background
- HTML + plain text email templates
- Retry logic with exponential backoff (3 retries: 60s → 120s → 240s)
- `BookingEmailLog` model tracks every email attempt
- Duplicate payment protection (409 Conflict)

### Frontend Website
- Movie listing with live filtering, sorting, pagination
- Visual seat map — click to select, shows booked seats in real time
- My Bookings page with stats
- Swagger UI at `/api/schema/swagger-ui/`

---

## Quick Start (Local)

### 1. Clone and setup
```bash
git clone <repo-url>
cd movie_booking
python3 -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Configure environment
```bash
cp .env.example .env
# Edit .env — set USE_SQLITE=True for local dev (no PostgreSQL needed)
```

### 3. Run migrations and seed data
```bash
python manage.py migrate
python manage.py seed_movies --count 50
python manage.py seed_bookings
python manage.py createsuperuser
```

### 4. Start the server
```bash
python manage.py runserver
```

Open: **http://127.0.0.1:8000**

### 5. Start Celery (optional — for background emails)
```bash
# In a separate terminal
redis-server                                          # Start Redis
celery -A movie_booking worker --loglevel=info        # Start Celery
```

---

## API Endpoints

| Method | URL | Description |
|--------|-----|-------------|
| GET | `/api/v1/movies/` | Movie list with filtering |
| GET | `/api/v1/movies/?genres=1,2&languages=1&sort=rating_desc` | Filtered movies |
| GET | `/api/v1/movies/<slug>/` | Movie detail |
| GET | `/api/v1/genres/` | Genres with movie counts |
| GET | `/api/v1/languages/` | Languages with movie counts |
| GET | `/api/v1/shows/` | Available shows |
| GET | `/api/v1/shows/<id>/` | Show detail |
| GET | `/api/v1/shows/<id>/booked-seats/` | Booked seat numbers |
| POST | `/api/v1/bookings/` | Create booking |
| GET | `/api/v1/bookings/list/` | My bookings |
| GET | `/api/v1/bookings/<ref>/` | Booking detail |
| GET | `/api/csrf/` | CSRF token for browser |

### Sample Booking Request
```json
POST /api/v1/bookings/
{
  "show": 1,
  "seats": ["A1", "A2", "B3"],
  "payment_id": "PAY_RAZORPAY_ABC123"
}
```

### Sample Movie List Response
```json
{
  "count": 5010,
  "total_pages": 251,
  "current_page": 1,
  "next": "http://localhost:8000/api/v1/movies/?page=2",
  "previous": null,
  "applied_filters": {"genres": "1,2", "sort": "rating_desc"},
  "genre_counts": [{"id": 1, "name": "Action", "count": 842}],
  "language_counts": [{"id": 1, "name": "Hindi", "count": 223}],
  "results": [...]
}
```

---

## Database Schema

```
Genre ──┐
        ├── Movie (M2M) ── Show ── Booking ── BookingEmailLog
Language┘                    │
                          Theater
```

### Indexes
- `movies`: rating, release_date, status, is_active, composite(is_active+rating)
- `shows`: show_datetime, (movie+show_datetime), (theater+show_datetime)
- `bookings`: (user+booked_at), status, payment_id, booking_reference

---

## Production Deployment

### Vercel + Neon PostgreSQL

1. Push to GitHub
2. Import repo at [vercel.com](https://vercel.com)
3. Add environment variables in Vercel dashboard:
```
DATABASE_URL=postgresql://user:pass@host/db?sslmode=require
SECRET_KEY=your-secret-key
DEBUG=False
REDIS_URL=rediss://...  (Upstash Redis)
CELERY_BROKER_URL=rediss://...
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.gmail.com
EMAIL_HOST_USER=your@email.com
EMAIL_HOST_PASSWORD=your-app-password
```
4. Deploy

> **Note:** Vercel serverless functions don't support long-running Celery workers.
> For production Celery, deploy the worker separately on Render, Railway, or a VPS.
> For demo/assignment, email sending falls back gracefully (logged, not blocking).

### Render / Railway
```bash
# Build command
pip install -r requirements.txt && python manage.py collectstatic --noinput && python manage.py migrate

# Start command (web)
gunicorn movie_booking.wsgi:application --bind 0.0.0.0:$PORT --workers 4

# Start command (worker)
celery -A movie_booking worker --loglevel=info
```

---

## Running Tests
```bash
python manage.py test movies bookings --verbosity=2
# 60 tests — all pass
```

## Admin Panel
```
http://127.0.0.1:8000/admin/
```
Create superuser: `python manage.py createsuperuser`

## API Documentation
```
http://127.0.0.1:8000/api/schema/swagger-ui/   ← Swagger UI
http://127.0.0.1:8000/api/schema/redoc/         ← ReDoc
```
