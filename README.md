# 🎬 Movie Booking Backend

A production-ready movie booking REST API built with Django and Django REST Framework. Supports multi-select genre/language filtering, atomic seat booking with overbooking protection, async email confirmations via Celery, and a full frontend UI.

Live on Railway · API Docs at `/api/schema/swagger-ui/`

---

## Tech Stack

| Layer | Technology |
|---|---|
| Backend | Django 4.2, Django REST Framework 3.15 |
| Database | PostgreSQL (SQLite for local dev) |
| Background Tasks | Celery 5.3 + Redis |
| Email | Django SMTP / Console backend |
| API Docs | drf-spectacular (Swagger UI + ReDoc) |
| Static Files | WhiteNoise |
| Production Server | Gunicorn |
| Deployment | Railway (Nixpacks) |

---

## Features

### Movie Catalogue
- Paginated movie list with 5000+ records
- Multi-select genre filtering — `?genres=1,2,3`
- Multi-select language filtering — `?languages=1,2`
- Sorting by rating, release date, title
- Full-text search by title and director — `?search=nolan`
- Status filter — `?status=now_showing`
- Dynamic filter counts — genre/language counts update based on active filters
- 15+ database indexes for query performance at scale
- Zero N+1 queries via `select_related` and `prefetch_related`

### Booking System
- Atomic booking creation with `select_for_update()` — prevents race conditions and overbooking
- Unique payment ID enforcement — 409 Conflict on duplicate payment
- Seat availability tracking per show
- Booking reference generation — human-readable format `BK-A3X9K2PQ`
- No authentication required — fully public API

### Email Confirmations
- Async email via Celery — API responds instantly, email sends in background
- HTML + plain text email templates
- Retry logic with exponential backoff — 3 retries at 60s → 120s → 240s
- `BookingEmailLog` model tracks every attempt (pending / sent / failed / retrying)
- Eager mode on Railway/Vercel — tasks run inline when no Redis worker available

### Frontend
- Movie listing page with live filtering, sorting, pagination
- Movie detail page with show times
- Visual seat map — click to select, booked seats shown in real time
- My Bookings page with booking history

---

## API Endpoints

### Movies
| Method | Endpoint | Description |
|---|---|---|
| GET | `/api/v1/movies/` | Paginated movie list |
| GET | `/api/v1/movies/?genres=1,2&sort=rating_desc` | Filtered + sorted movies |
| GET | `/api/v1/movies/?search=inception&status=now_showing` | Search + status filter |
| GET | `/api/v1/movies/<slug>/` | Movie detail |
| GET | `/api/v1/genres/` | All genres with movie counts |
| GET | `/api/v1/languages/` | All languages with movie counts |

### Shows & Bookings
| Method | Endpoint | Description |
|---|---|---|
| GET | `/api/v1/shows/` | Available shows |
| GET | `/api/v1/shows/<id>/` | Show detail |
| GET | `/api/v1/shows/<id>/booked-seats/` | Booked seat numbers for a show |
| POST | `/api/v1/bookings/` | Create a booking |
| GET | `/api/v1/bookings/list/` | All bookings |
| GET | `/api/v1/bookings/<ref>/` | Booking detail by reference |

### Utility
| Method | Endpoint | Description |
|---|---|---|
| GET | `/api/csrf/` | CSRF token for browser JS |
| GET | `/api/schema/swagger-ui/` | Interactive API docs |
| GET | `/api/schema/redoc/` | ReDoc API docs |
| GET | `/admin/` | Django admin panel |

---

## Request & Response Examples

### Create Booking
```http
POST /api/v1/bookings/
Content-Type: application/json

{
  "show": 1,
  "seats": ["A1", "A2", "B3"],
  "payment_id": "PAY_RAZORPAY_ABC123"
}
```

```json
{
  "success": true,
  "message": "Booking confirmed! Confirmation email will be sent shortly.",
  "data": {
    "booking_reference": "BK-A3X9K2PQ",
    "status": "confirmed",
    "seats": ["A1", "A2", "B3"],
    "seat_count": 3,
    "total_amount": "750.00",
    "booked_at": "2026-05-21T11:40:35+05:30"
  }
}
```

### Movie List Response
```json
{
  "count": 5030,
  "total_pages": 252,
  "current_page": 1,
  "next": "/api/v1/movies/?page=2",
  "previous": null,
  "applied_filters": { "genres": "1,2", "sort": "rating_desc" },
  "genre_counts": [
    { "id": 1, "name": "Action", "count": 842 },
    { "id": 2, "name": "Drama", "count": 631 }
  ],
  "language_counts": [
    { "id": 1, "name": "Hindi", "count": 223 }
  ],
  "results": [ ... ]
}
```

---

## Database Schema

```
Genre ──┐
        ├──(M2M)── Movie ──── Show ──── Booking ──── BookingEmailLog
Language┘            │          │
                  (slug)     Theater
```

### Models
- **Genre** — movie categories (Action, Drama, Comedy...)
- **Language** — available languages (Hindi, English, Tamil...)
- **Movie** — core entity with M2M to Genre and Language
- **Theater** — physical cinema location
- **Show** — a specific screening (movie + theater + datetime + format)
- **Booking** — user's ticket (show + seats + payment_id)
- **BookingEmailLog** — tracks email delivery per booking

### Index Strategy
- `movies`: rating, release_date, status, is_active, composite(is_active+rating), composite(is_active+release_date)
- `shows`: show_datetime, (movie+show_datetime), (theater+show_datetime)
- `bookings`: (user+booked_at), status, payment_id, booking_reference

---

## Local Development

### Prerequisites
- Python 3.11+
- Git

### Setup

```bash
# 1. Clone the repo
git clone https://github.com/DharmBanker/movie-booking.git
cd movie-booking

# 2. Create virtual environment
python3 -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Configure environment
cp .env.example .env
# .env already has USE_SQLITE=True — no PostgreSQL needed for local dev
```

### Run

```bash
# Apply migrations
python manage.py migrate

# Create the app user (dharm / dharm1234)
python manage.py create_app_user

# Seed movie data (5000+ movies)
python manage.py seed_movies

# Seed booking data (optional)
python manage.py seed_bookings

# Start the server
python manage.py runserver
```

Open **http://127.0.0.1:8000**

### Admin Panel
```
URL:      http://127.0.0.1:8000/admin/
Username: dharm
Password: dharm1234
```

### Celery (optional — for background email sending)
```bash
# Terminal 1 — Redis
redis-server

# Terminal 2 — Celery worker
celery -A movie_booking worker --loglevel=info
```

Without Redis, set `USE_CELERY_EAGER=True` in `.env` — emails send synchronously inline.

---

## Deployment — Railway

This project is configured for Railway with Nixpacks. Zero config needed beyond environment variables.

### Steps

1. Go to [railway.app](https://railway.app) → login with GitHub
2. **New Project** → **Deploy from GitHub repo** → select `DharmBanker/movie-booking`
3. Click **New** → **Database** → **Add PostgreSQL** — Railway sets `DATABASE_URL` automatically
4. Add these environment variables in Railway → Variables tab:

| Variable | Value |
|---|---|
| `SECRET_KEY` | A strong 50-character random string |
| `DEBUG` | `False` |
| `USE_CELERY_EAGER` | `True` |
| `EMAIL_BACKEND` | `django.core.mail.backends.console.EmailBackend` |

5. Railway auto-deploys. The build runs:
   - `pip install -r requirements.txt`
   - `python manage.py migrate`
   - `python manage.py create_app_user`
   - `python manage.py collectstatic`

### Environment Variables Reference

| Variable | Required | Description |
|---|---|---|
| `SECRET_KEY` | ✅ | Django secret key — keep private |
| `DEBUG` | ✅ | `False` in production |
| `DATABASE_URL` | ✅ | PostgreSQL connection string (auto-set by Railway) |
| `USE_CELERY_EAGER` | ✅ | `True` on Railway (no Redis worker) |
| `EMAIL_BACKEND` | ✅ | SMTP backend for real emails |
| `EMAIL_HOST_USER` | optional | Gmail address for sending emails |
| `EMAIL_HOST_PASSWORD` | optional | Gmail app password |
| `FRONTEND_URL` | optional | Your Railway deployment URL |

---

## Project Structure

```
movie-booking/
├── movie_booking/          # Django project config
│   ├── settings.py         # Environment-aware settings
│   ├── urls.py             # Root URL config
│   ├── wsgi.py             # WSGI entry point
│   └── celery.py           # Celery app config
│
├── movies/                 # Movies app
│   ├── models.py           # Genre, Language, Movie
│   ├── views.py            # MovieListView, MovieDetailView, GenreListView, LanguageListView
│   ├── serializers.py      # DRF serializers
│   ├── services.py         # MovieQueryService, GenreService, LanguageService
│   ├── filters.py          # django-filter FilterSet
│   ├── pagination.py       # StandardResultsPagination
│   └── management/commands/seed_movies.py
│
├── bookings/               # Bookings app
│   ├── models.py           # Theater, Show, Booking, BookingEmailLog
│   ├── views.py            # BookingCreateView, ShowListView, etc.
│   ├── serializers.py      # DRF serializers
│   ├── services.py         # BookingService (atomic booking creation)
│   ├── tasks.py            # Celery email task with retry logic
│   └── management/commands/
│       ├── create_app_user.py   # Creates dharm user at deploy time
│       └── seed_bookings.py
│
├── frontend/               # Frontend app (Django templates)
│   ├── views.py
│   └── urls.py
│
├── templates/
│   ├── frontend/           # HTML pages
│   └── emails/             # Email templates (HTML + plain text)
│
├── static/                 # CSS, JS assets
├── Procfile                # Gunicorn start command
├── nixpacks.toml           # Railway build config
├── railway.json            # Railway deploy config
├── vercel.json             # Vercel config (kept for reference)
├── build_files.sh          # Build script
└── requirements.txt        # Pinned Python dependencies
```

---

## Author

**Dharm Banker**
GitHub: [@DharmBanker](https://github.com/DharmBanker)
