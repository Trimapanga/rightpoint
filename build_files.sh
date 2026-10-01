#!/bin/bash
# Vercel build script for the Django app.
# Runs before static files are uploaded.
set -e

pip install --break-system-packages -r requirements.txt
python manage.py collectstatic --noinput
python manage.py migrate --noinput
# Nest collected files under static/ so Vercel CDN serves them at /static/*
mkdir -p dist/static
cp -r staticroot/* dist/static/
