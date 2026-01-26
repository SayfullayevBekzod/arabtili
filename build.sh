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

# Import initial data
echo "📥 Initializing data..."
python manage.py seed_all

# Extra: Import from database_export.json if exists and needed
if [ -f "database_export.json" ]; then
    echo "📦 database_export.json topildi. Import qilinmoqdami? (Word count checking...)"
    WORD_COUNT=$(python manage.py shell -c "from arab.models import Word; print(Word.objects.count())" 2>/dev/null || echo "0")
    if [ "$WORD_COUNT" -lt "200" ]; then
        python migrate_to_postgres.py import database_export.json
    fi
fi

echo "✅ Build completed successfully!"
