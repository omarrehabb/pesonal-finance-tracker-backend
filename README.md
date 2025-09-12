# Personal Finance Tracker — Backend (Django)

## Overview
This repository contains the backend API for the Personal Finance Tracker application. It provides secure authentication, budgeting, transactions, and a demo open‑banking integration. The backend is built with Django and Django REST Framework and serves the React frontend as a single origin in production.

## Key Features
- Authentication: Session-based login, CSRF protection, optional 2FA (django-two-factor-auth)
- Transactions: CRUD operations with income/expense summaries
- Budgets: Create and manage budget categories with aggregated reports
- Open Banking (demo): Simulated bank connections and imports
- Single-Origin Deployment: Backend and frontend served together using Whitenoise

## Tech Stack
- Frameworks: Django 5, Django REST Framework
- Auth & Security: django-otp, django-two-factor-auth, CSRF protection
- Static & Deployment: Whitenoise (static files), Gunicorn (WSGI server)
- Database: SQLite (local), PostgreSQL (production via dj-database-url)
- CI/CD & Hosting: Docker + Fly.io (GitHub Actions workflow included)

## Local Development
1. Create and activate a virtual environment
```bash
python3 -m venv venv
source venv/bin/activate
```

2. Install dependencies
```bash
pip install -r requirements.txt
```

3. Run migrations and start server
```bash
python manage.py migrate
python manage.py runserver
```

API base:
- Dev: frontend → http://localhost:8000
- Prod: same-origin (no CORS required)

## Environment Variables
- DJANGO_SECRET_KEY (required in production)
- DJANGO_DEBUG (true for dev, false for production)
- DJANGO_ALLOWED_HOSTS (comma-separated hostnames)
- DATABASE_URL (Postgres connection string; optional for local SQLite)

## Project Structure
```
backend/          # Django project (settings, urls, wsgi)
core/             # Serves SPA entry point
transactions/     # Transactions API, user profiles, auth helpers
budgets/          # Budget API and summaries
banking/          # Demo open banking endpoints
requirements.txt  # Python dependencies
```

## Deployment (Fly.io Example)
The included GitHub Actions workflow builds frontend + backend into one Docker image and deploys to Fly.io.

Secrets needed:
- FLY_API_TOKEN, FLY_APP_NAME, DJANGO_SECRET_KEY, DATABASE_URL

After the first deploy, run database migrations:
```bash
fly ssh console -C "python /app/manage.py migrate"
```

## API Highlights
- Auth: `/api-auth/login/`, `/api-auth/logout/`
- Register: `POST /api/auth/register/`
- Profile: `GET /api/profiles/my_profile/`
- Transactions: `/api/transactions/`, `/api/transactions/summary/`
- Budgets: `/api/budgets/...`

