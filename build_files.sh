#!/bin/bash
# Vercel build script for the Django app.
# Runs before static files are uploaded.
set -e

pip install -r requirements.txt
python manage.py collectstatic --noinput
