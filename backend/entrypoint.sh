#!/bin/sh
set -e

python manage.py migrate --noinput
python manage.py collectstatic --noinput
python manage.py load_ingredients

exec gunicorn foodgram_backend.wsgi:application --bind 0.0.0.0:8000
