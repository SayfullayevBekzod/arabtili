# Neon PostgreSQL Database Setup

## 1. Neon Database yaratish

1. [Neon Console](https://console.neon.tech) ga kiring
2. "Create Project" bosing
3. Project nomi: `arabtili` (yoki istalgan nom)
4. Region: `AWS / US East (Ohio)` yoki yaqin region
5. "Create Project" bosing

## 2. Connection String olish

Neon dashboard dan **Connection String** ni nusxalang. U quyidagicha ko'rinadi:

```
postgresql://username:password@ep-xxx-xxx.us-east-2.aws.neon.tech/neondb?sslmode=require
```

## 3. Local testlash (ixtiyoriy)

`.env` fayl yarating:

```bash
DATABASE_URL=postgresql://username:password@ep-xxx-xxx.us-east-2.aws.neon.tech/neondb?sslmode=require
DJANGO_DEBUG=True
```

Keyin ishga tushiring:

```bash
pip install python-dotenv
python manage.py migrate
python migrate_to_postgres.py import database_export.json
python manage.py runserver
```

## 4. Production Deploy (Vercel/Render/Railway)

### Vercel uchun:

1. Vercel dashboard ga kiring
2. Project Settings → Environment Variables
3. Qo'shing:
   - `DATABASE_URL` = `postgresql://...` (Neon connection string)
   - `DJANGO_SECRET_KEY` = `your-secret-key`
   - `DJANGO_DEBUG` = `False`

4. Deploy:
```bash
git add .
git commit -m "Add Neon database"
git push
```

5. Vercel console orqali migratsiya:
```bash
# Vercel CLI orqali
vercel env pull
python manage.py migrate
python migrate_to_postgres.py import database_export.json
```

### Railway uchun:

1. Railway dashboard → New Project
2. "Deploy from GitHub repo" tanlang
3. Environment Variables:
   - `DATABASE_URL` = Neon connection string
   - `DJANGO_SECRET_KEY` = random key
   - `DJANGO_DEBUG` = `False`

4. Deploy avtomatik boshlanadi
5. Railway console orqali:
```bash
python manage.py migrate
python migrate_to_postgres.py import database_export.json
```

### Render uchun:

1. `render.yaml` da `DATABASE_URL` o'rniga Neon connection string kiriting
2. Environment Variables:
   - `DATABASE_URL` = Neon connection string
3. Deploy qiling

## 5. Ma'lumotlarni yuklash

Deploy qilingandan keyin:

```bash
# Platform console orqali (Vercel/Railway/Render)
python manage.py migrate
python migrate_to_postgres.py import database_export.json
python manage.py createsuperuser
```

## 6. Tekshirish

```bash
# Database connection tekshirish
python manage.py dbshell

# Yoki
python manage.py shell
>>> from arab.models import Word
>>> Word.objects.count()
393  # Muvaffaqiyatli!
```

## Neon Afzalliklari

✅ **Bepul**: 0.5 GB storage, 1 database  
✅ **Tez**: Serverless PostgreSQL  
✅ **Oson**: Connection string yetarli  
✅ **Ishonchli**: Avtomatik backup  
✅ **Masshtablanadi**: Kerak bo'lganda kengayadi  

## Muammolar

### "database is locked"
- SQLite bilan bog'liq, Neon ishlatganda yo'qoladi

### "SSL connection required"
- Connection string oxirida `?sslmode=require` borligiga ishonch hosil qiling

### "too many connections"
- `conn_max_age=600` settings.py da allaqachon sozlangan ✅
