#!/usr/bin/env bash
# exit on error
set -o errexit

pip install -r requirements.txt

python manage.py collectstatic --no-input
python manage.py migrate

# Load fixtures if they exist
python manage.py loaddata arab/fixtures/arabic_basics.json --ignorenonexistent || true
python manage.py loaddata arab/fixtures/tajweed_seed.json --ignorenonexistent || true
