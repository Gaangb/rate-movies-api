#!/usr/bin/env sh
set -e

python manage.py collectstatic --noinput || true
python manage.py makemigrations --noinput
python manage.py migrate --noinput

exec "$@"
