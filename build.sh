#!/usr/bin/env bash
# Build script for deployment (Render, Railway, etc.)

set -o errexit  # Exit on error

echo "🚀 Starting build process..."

# Install dependencies
echo "📦 Installing dependencies..."
pip install -r requirements.txt

# Collect static files
echo "📁 Collecting static files..."
python manage.py collectstatic --noinput

# Run migrations
echo "🔄 Running database migrations..."
python manage.py migrate --noinput

# Import initial data (if database is empty)
echo "📥 Checking for initial data..."
WORD_COUNT=$(python manage.py shell -c "from arab.models import Word; print(Word.objects.count())" 2>/dev/null || echo "0")

if [ "$WORD_COUNT" -eq "0" ]; then
    echo "📚 Database is empty. Importing initial data..."
    if [ -f "database_export.json" ]; then
        python migrate_to_postgres.py import database_export.json
        echo "✅ Initial data imported successfully!"
    else
        echo "⚠️  database_export.json not found. Skipping data import."
    fi
else
    echo "✅ Database already has $WORD_COUNT words. Skipping import."
fi

echo "✅ Build completed successfully!"
