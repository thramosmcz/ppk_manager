#!/usr/bin/env bash

export SQLITE_PATH=./data/db.sqlite3

python manage.py migrate
python manage.py runserver 0.0.0.0:8000
