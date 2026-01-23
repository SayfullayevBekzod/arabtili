release: python manage.py migrate && python manage.py loaddata arab/fixtures/arabic_basics.json arab/fixtures/tajweed_seed.json --ignorenonexistent
web: gunicorn config.wsgi:application --workers 4 --threads 2 --worker-class gthread --bind 0.0.0.0:$PORT
