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
python manage.py seed_all || echo "⚠️ seed_all may have partial errors, continuing..."

# Always import from database_export.json to ensure full data
if [ -f "database_export.json" ]; then
    echo "📦 Importing database_export.json..."
    python migrate_to_postgres.py import database_export.json || echo "⚠️ Import may have some conflicts, continuing..."
fi

echo "✅ Build completed successfully!"

