#!/usr/bin/env bash

python manage.py migrate
exec gunicorn pkproject.wsgi:application --bind 0.0.0.0:${PORT:-8000}
