web: gunicorn config.wsgi --log-file - --workers 3
release: python manage.py migrate --noinput && python migrate_to_postgres.py import database_export.json || echo "Data already imported"
