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
    DJANGO_SETTINGS_MODULE=backend.settings \
    WEB_CONCURRENCY=1 \
    GUNICORN_THREADS=2 \
    GUNICORN_MAX_REQUESTS=1000 \
    GUNICORN_MAX_REQUESTS_JITTER=100 \
    GUNICORN_TIMEOUT=60

WORKDIR /app

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
    sed -i 's/<title>React App<\/title>/<title>Personal Finance Tracker<\/title>/g' templates/core/index.html && \
    if [ -d frontend_build/static ]; then cp -r frontend_build/static/* static/; fi

# Collect static (no-op in dev, used in prod with Whitenoise)
RUN python manage.py collectstatic --noinput || true

EXPOSE 8000
# Use env-driven Gunicorn settings and keep workers low for small VMs
CMD ["sh", "-c", "exec gunicorn backend.wsgi:application --bind 0.0.0.0:${PORT:-8000} --workers ${WEB_CONCURRENCY:-1} --threads ${GUNICORN_THREADS:-2} --max-requests ${GUNICORN_MAX_REQUESTS:-1000} --max-requests-jitter ${GUNICORN_MAX_REQUESTS_JITTER:-100} --timeout ${GUNICORN_TIMEOUT:-60} --keep-alive 5 --worker-tmp-dir /dev/shm"]
