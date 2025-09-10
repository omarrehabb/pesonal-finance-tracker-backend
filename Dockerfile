# Multi-stage Dockerfile building the React frontend, then serving with Django

# 1) Build frontend from GitHub
FROM node:18-alpine AS frontend-build
ARG FRONTEND_REPO="https://github.com/omarrehabb/personal-finance-tracker-frontend.git"
WORKDIR /src
RUN apk add --no-cache git
RUN git clone --depth=1 "$FRONTEND_REPO" frontend
WORKDIR /src/frontend
RUN npm ci --no-audit --no-fund
# Use same-origin API in production
ENV REACT_APP_API_BASE=
RUN npm run build

# 2) Python backend image
FROM python:3.11-slim AS backend
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    DJANGO_SETTINGS_MODULE=backend.settings

WORKDIR /app

# System deps for psycopg2
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential libpq-dev \
  && rm -rf /var/lib/apt/lists/*

# Install python deps
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend source
COPY . ./

# Bring in the built frontend
COPY --from=frontend-build /src/frontend/build ./frontend_build

# Prepare templates/static: serve SPA via Django template and Whitenoise
RUN mkdir -p templates/core static && \
    cp -f frontend_build/index.html templates/core/index.html && \
    if [ -d frontend_build/static ]; then cp -r frontend_build/static/* static/; fi

# Collect static (no-op in dev, used in prod with Whitenoise)
RUN python manage.py collectstatic --noinput || true

EXPOSE 8000
CMD ["gunicorn", "backend.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "3"]

