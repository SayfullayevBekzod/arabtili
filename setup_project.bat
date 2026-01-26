@echo off
setlocal

echo 🚀 Starting project setup...

:: 1. Check for virtual environment
if exist "env\Scripts\activate.bat" (
    echo 📦 Activating virtual environment...
    call env\Scripts\activate.bat
) else (
    echo ⚠️  Virtual environment (env) not found. Skipping activation.
)

:: 2. Install requirements
echo 📦 Installing dependencies...
pip install -r requirements.txt

:: 3. Run migrations
echo 🔄 Running database migrations...
python manage.py migrate --noinput

:: 4. Initialize Data
echo 📥 Loading all project data...
python manage.py init_data

:: 5. Collect static
echo 📁 Collecting static files...
python manage.py collectstatic --noinput

echo.
echo ✅ Setup completed successfully!
echo 💡 Run 'python manage.py runserver' to start the project.

pause
