#!/usr/bin/env bash
# exit on error
set -o errexit

pip install -r requirements.txt

python manage.py collectstatic --no-input
python manage.py migrate

# Sync dictionary from JSON
echo "Syncing dictionary from dictionary.json..."
python manage.py sync_dictionary

# Load fixtures if they exist
# Load ALL JSON fixtures automatically
echo "Loading all fixtures..."
for file in arab/fixtures/*.json; do
    if [ -f "$file" ]; then
        echo "Loading $file..."
        python manage.py loaddata "$file" --ignorenonexistent || true
    fi
done

# Create superuser
echo "from django.contrib.auth import get_user_model; User = get_user_model(); User.objects.create_superuser('admin', 'admin@example.com', 'admin') if not User.objects.filter(username='admin').exists() else print('Admin already exists')" | python manage.py shell
