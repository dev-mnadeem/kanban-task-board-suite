#!/bin/sh
set -eu

# Django's own tables (sessions, auth, admin). The original entrypoint never
# ran these, so /admin/ returned "no such table: django_session".
python manage.py migrate --noinput

# Idempotent: creates the DynamoDB Card table only if it is missing.
python manage.py init_dynamodb

exec "$@"
