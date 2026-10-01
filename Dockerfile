FROM python:3.12-slim AS base

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    DJANGO_SETTINGS_MODULE=config.settings

WORKDIR /app

# libpjpeg/zlib for image handling, psycopg build deps come from the wheel.
RUN apt-get update \
    && apt-get install -y --no-install-recommends libjpeg62-turbo zlib1g curl \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt ./
RUN pip install --upgrade pip && pip install -r requirements.txt

COPY . .

# Fail the build on a missing manifest rather than at request time.
RUN DJANGO_DEBUG=False DJANGO_SECRET_KEY=build-only-key-please-replace-0123456789abcdef \
    python manage.py collectstatic --noinput

RUN adduser --disabled-password --gecos "" appuser && chown -R appuser /app
USER appuser

EXPOSE 8000
# Shell form so $PORT is expanded by platforms that inject it (Render, Fly, Heroku).
CMD gunicorn config.wsgi:application --bind "0.0.0.0:${PORT:-8000}" --workers "${WEB_CONCURRENCY:-3}" --threads 2 --timeout 60 --access-logfile - --error-logfile -
