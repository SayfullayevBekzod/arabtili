# Deployment Instructions

## ⚡ AVTOMATIK MA'LUMOTLARNI KO'CHIRISH

### SQLite → PostgreSQL migratsiya (1055 ta obyekt)

**Hozirgi holatda:**
- ✅ `database_export.json` fayli tayyor (1055 ta obyekt)
- ✅ 393 ta so'z
- ✅ 467 ta kategoriya
- ✅ 28 ta harf
- ✅ 48 ta tajvid qoidasi
- ✅ Va boshqalar...

**Deploy qilgandan keyin (PostgreSQL da):**
```bash
# 1. Migratsiyalarni qo'llash
python manage.py migrate

# 2. BARCHA ma'lumotlarni yuklash (AVTOMATIK!)
python manage.py seed_all

# 3. Superuser yaratish
python manage.py createsuperuser
```

**Heroku uchun:**
```bash
# database_export.json faylini yuklash
git add database_export.json migrate_to_postgres.py
git commit -m "Add database export"
git push heroku main

# Ma'lumotlarni yuklash
heroku run python migrate_to_postgres.py import database_export.json
```

---

## PostgreSQL sozlash

### 1. PostgreSQL o'rnatish
```bash
# Heroku yoki boshqa platformada avtomatik o'rnatiladi
```

### 2. Environment variables
```bash
DATABASE_URL=postgresql://user:password@host:port/dbname
DJANGO_DEBUG=False
DJANGO_SECRET_KEY=your-secret-key-here
```

### 3. Database migratsiya
```bash
# Migratsiyalarni qo'llash
python manage.py migrate

# Superuser yaratish
python manage.py createsuperuser

# Static fayllarni to'plash
python manage.py collectstatic --noinput
```

### 4. Ma'lumotlarni yuklash

#### Variant A: Admin panel orqali
1. `/admin` ga kiring
2. `Words` bo'limiga o'ting
3. JSON fayllarni import qiling (words1.json, words2.json, etc.)

#### Variant B: Script orqali
```bash
python import_custom_json.py words1.json
python import_custom_json.py words2.json
python import_custom_json.py words3.json
python import_custom_json.py words4.json
```

## Heroku Deploy

### 1. Heroku CLI o'rnatish
```bash
# https://devcenter.heroku.com/articles/heroku-cli
```

### 2. Loyihani deploy qilish
```bash
# Git repo yaratish
git init
git add .
git commit -m "Initial commit"

# Heroku app yaratish
heroku create your-app-name

# PostgreSQL qo'shish
heroku addons:create heroku-postgresql:essential-0

# Environment variables sozlash
heroku config:set DJANGO_SECRET_KEY="$(python -c 'from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())')"
heroku config:set DJANGO_DEBUG=False

# Deploy
git push heroku main

# Migratsiya
heroku run python manage.py migrate
heroku run python manage.py createsuperuser

# Ma'lumotlarni yuklash
heroku run python manage.py seed_all
```

## Render.com Deploy

### 1. render.yaml yaratish (avtomatik)
Loyihada `render.yaml` fayli mavjud.

### 2. Render.com da
1. GitHub repo ulang
2. "New Web Service" bosing
3. Repo tanlang
4. Environment variables qo'shing
5. Deploy bosing

### 3. Ma'lumotlarni yuklash
```bash
# Render shell orqali
python manage.py seed_all
```
