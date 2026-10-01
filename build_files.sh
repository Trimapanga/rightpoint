#!/bin/bash
# Vercel build script for the Django app.
# Runs after Vercel's Python builder installs requirements.
set -e

python manage.py migrate --noinput
python manage.py collectstatic --noinput
