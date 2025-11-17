#!/bin/bash

echo "Running makemigrations..."
python manage.py makemigrations --noinput

echo "Running migrate..."
python manage.py migrate --noinput

echo "Starting Gunicorn..."
exec gunicorn inventory.wsgi:application --bind 0.0.0.0:8000 --workers 3
