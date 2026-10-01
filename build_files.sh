#!/bin/bash
# Vercel build script for the Django app.
# Runs before static files are uploaded.
set -e

pip install --break-system-packages -r requirements.txt
python manage.py collectstatic --noinput
