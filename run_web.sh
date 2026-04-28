#!/usr/bin/env bash

python manage.py migrate
gunicorn pkproject.wsgi:application --bind 0.0.0.0:$PORT
