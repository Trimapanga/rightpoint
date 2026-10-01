release: python manage.py migrate --noinput
web: gunicorn config.wsgi:application --bind :$PORT --workers 3 --threads 2 --timeout 60 --access-logfile -
