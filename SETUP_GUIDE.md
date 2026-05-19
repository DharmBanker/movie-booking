# Movie Booking Backend — Complete Setup Guide

## Tech Stack
- Python 3.11+
- Django 4.2
- Django REST Framework
- PostgreSQL
- Celery + Redis
- SMTP Email

---

## Step 1 — Install Python

### macOS
```bash
brew install python@3.11
python3 --version
```

### Ubuntu/Debian
```bash
sudo apt update
sudo apt install python3.11 python3.11-venv python3.11-dev
python3 --version
```

### Windows
Download from https://www.python.org/downloads/ and check "Add to PATH"

---

## Step 2 — Install pip

```bash
python3 -m ensurepip --upgrade
pip3 --version
```

---

## Step 3 — Install virtualenv

```bash
pip3 install virtualenv
virtualenv --version
```

---

## Step 4 — Install PostgreSQL

### macOS
```bash
brew install postgresql@15
brew services start postgresql@15
```

### Ubuntu/Debian
```bash
sudo apt install postgresql postgresql-contrib
sudo systemctl start postgresql
sudo systemctl enable postgresql
```

### Windows
Download from https://www.postgresql.org/download/windows/

### Create Database and User
```bash
# macOS/Linux
sudo -u postgres psql

# Inside psql shell:
CREATE DATABASE movie_booking_db;
CREATE USER movie_user WITH PASSWORD 'your_secure_password';
GRANT ALL PRIVILEGES ON DATABASE movie_booking_db TO movie_user;
ALTER USER movie_user CREATEDB;
\q
```

---

## Step 5 — Install Redis

### macOS
```bash
brew install redis
brew services start redis
redis-cli ping   # Should return PONG
```

### Ubuntu/Debian
```bash
sudo apt install redis-server
sudo systemctl start redis
sudo systemctl enable redis
redis-cli ping
```

### Windows
Download from https://github.com/microsoftarchive/redis/releases

---

## Step 6 — Create Virtual Environment

```bash
cd /path/to/your/projects
virtualenv venv --python=python3.11
```

---

## Step 7 — Activate Virtual Environment

### macOS/Linux
```bash
source venv/bin/activate
```

### Windows
```bash
venv\Scripts\activate
```

You should see `(venv)` in your terminal prompt.

---

## Step 8-12 — Install All Python Dependencies

```bash
pip install django==4.2.13
pip install djangorestframework==3.15.1
pip install psycopg2-binary==2.9.9
pip install celery==5.3.6
pip install redis==5.0.3
pip install django-filter==23.5
pip install python-dotenv==1.0.1
pip install django-celery-results==2.5.1
pip install django-celery-beat==2.6.0
pip install Pillow==10.3.0
pip install gunicorn==21.2.0
pip install whitenoise==6.6.0
pip install drf-spectacular==0.27.2
```

Or install all at once:
```bash
pip install -r requirements.txt
```

---

## Step 13 — Configure Environment Variables

```bash
cp .env.example .env
# Edit .env with your actual values
nano .env
```

---

## Step 14 — Run Migrations

```bash
cd movie_booking
python manage.py makemigrations
python manage.py migrate
python manage.py createsuperuser
```

---

## Step 15 — Start Redis Server

```bash
# macOS
brew services start redis

# Linux
sudo systemctl start redis

# Or run directly
redis-server
```

---

## Step 16 — Start Celery Worker

Open a new terminal, activate venv, then:
```bash
cd movie_booking
celery -A movie_booking worker --loglevel=info --concurrency=4
```

For Celery Beat (scheduled tasks):
```bash
celery -A movie_booking beat --loglevel=info
```

---

## Step 17 — Run Django Development Server

```bash
python manage.py runserver 0.0.0.0:8000
```

---

## API Documentation

Once running, visit:
- Swagger UI: http://localhost:8000/api/schema/swagger-ui/
- ReDoc: http://localhost:8000/api/schema/redoc/
- Admin: http://localhost:8000/admin/

---

## Production Deployment Notes

```bash
# Collect static files
python manage.py collectstatic

# Run with gunicorn
gunicorn movie_booking.wsgi:application --bind 0.0.0.0:8000 --workers 4

# Run Celery in production
celery -A movie_booking worker --loglevel=warning --concurrency=8 -D
```
