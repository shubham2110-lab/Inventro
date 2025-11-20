#!/bin/bash

echo "Running makemigrations..."
python manage.py makemigrations --noinput

echo "Running migrate..."
python manage.py migrate --noinput

echo "Creating Superuser..."
python manage.py createsuperuser --noinput 

echo "Starting Gunicorn..."
exec gunicorn inventro.wsgi:application --bind 0.0.0.0:8000 --workers 3
