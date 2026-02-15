# 🐳 הפעלה מקומית עם Docker

מדריך מלא להפעלת המערכת על המחשב שלך.

---

## דרישות מקדימות

### 1. התקן Docker Desktop

**Windows**:
1. הורד מ-[docker.com/products/docker-desktop](https://www.docker.com/products/docker-desktop/)
2. הפעל את המתקין
3. אפשר WSL 2 כשמתבקש
4. אתחל את המחשב
5. פתח Docker Desktop ווודא שהוא רץ (אייקון בשורת המשימות)

**Mac**:
1. הורד Docker Desktop ל-Mac
2. גרור ל-Applications
3. פתח והפעל

**Linux**:
```bash
# Ubuntu/Debian
sudo apt update
sudo apt install docker.io docker-compose
sudo systemctl start docker
sudo usermod -aG docker $USER
```

### 2. ודא ש-Docker רץ

```bash
docker --version
# צריך להציג: Docker version 24.x.x

docker-compose --version
# צריך להציג: Docker Compose version 2.x.x
```

---

## שלב 1: הכן קבצי הגדרות

### 1.1 צור קובץ `.env`

```bash
cd C:\Users\steve\Documents\Profiler
copy .env.example .env
```

### 1.2 ערוך את `.env`

פתח את `C:\Users\steve\Documents\Profiler\.env` בעורך טקסט ועדכן:

```bash
# ── PostgreSQL ──────────────────────────────────────────
POSTGRES_USER=wallet_user
POSTGRES_PASSWORD=change_this_password_123!
POSTGRES_DB=wallet_intel

# ── RPC Endpoints (חובה!) ──────────────────────────────
# קבל מפתחות חינמיים מ-Alchemy.com
ETHEREUM_RPC_URL=https://eth-mainnet.g.alchemy.com/v2/YOUR_ALCHEMY_KEY
BASE_RPC_URL=https://base-mainnet.g.alchemy.com/v2/YOUR_ALCHEMY_KEY
ARBITRUM_RPC_URL=https://arb-mainnet.g.alchemy.com/v2/YOUR_ALCHEMY_KEY
POLYGON_RPC_URL=https://polygon-mainnet.g.alchemy.com/v2/YOUR_ALCHEMY_KEY
SOLANA_RPC_URL=https://api.mainnet-beta.solana.com

# ── Optional: CoinGecko Pro API Key ───────────────────
COINGECKO_API_KEY=

# ── Admin API ─────────────────────────────────────────
ADMIN_API_KEY=super-secret-admin-key-change-me

# ── Website Password Protection ──────────────────────
SITE_PASSWORD=wallet123
```

**חשוב**:
- ⚠️ שנה את `POSTGRES_PASSWORD` לסיסמה חזקה!
- ⚠️ שנה את `ADMIN_API_KEY` למפתח אקראי ארוך!
- ⚠️ שנה את `SITE_PASSWORD` לסיסמה שתרצה לאתר!
- ⚠️ קבל מפתחות Alchemy (בחינם): [dashboard.alchemy.com](https://dashboard.alchemy.com)

---

## שלב 2: הרם את המערכת

### 2.1 Build והפעלה

```bash
cd C:\Users\steve\Documents\Profiler

# Build all containers (זמן: 5-10 דקות בפעם הראשונה)
docker-compose up --build -d
```

הפקודה תעלה 6 שירותים:
1. **PostgreSQL** - מסד נתונים
2. **Redis** - זיכרון מטמון
3. **Backend API** - FastAPI server
4. **Celery Worker** - עיבוד ניתוחים
5. **Celery Beat** - עדכוני sanctions אוטומטיים
6. **Frontend** - Next.js web interface

### 2.2 בדוק שהכל רץ

```bash
# בדוק שכל 6 השירותים רצים
docker-compose ps

# צריך להראות:
# NAME                          STATUS
# profiler-db-1                 Up
# profiler-redis-1              Up
# profiler-api-1                Up
# profiler-worker-1             Up
# profiler-beat-1               Up
# profiler-frontend-1           Up
```

### 2.3 בדוק לוגים

```bash
# לוגים של כל השירותים
docker-compose logs -f

# לוגים של שירות ספציפי
docker-compose logs -f api
docker-compose logs -f worker
docker-compose logs -f frontend
```

---

## שלב 3: אתחול מסד הנתונים

### 3.1 הוסף עמודות חדשות למעקב זמן

```bash
# התחבר למסד הנתונים
docker exec -it profiler-db-1 psql -U wallet_user -d wallet_intel

# הרץ בתוך psql:
ALTER TABLE analysis_jobs ADD COLUMN IF NOT EXISTS started_at TIMESTAMPTZ;
ALTER TABLE analysis_jobs ADD COLUMN IF NOT EXISTS completed_at TIMESTAMPTZ;
ALTER TABLE analysis_jobs ADD COLUMN IF NOT EXISTS analysis_duration_seconds FLOAT;

# יציאה
\q
```

**Or** - הרץ באחת:

```bash
docker exec -it profiler-db-1 psql -U wallet_user -d wallet_intel -c "
ALTER TABLE analysis_jobs ADD COLUMN IF NOT EXISTS started_at TIMESTAMPTZ;
ALTER TABLE analysis_jobs ADD COLUMN IF NOT EXISTS completed_at TIMESTAMPTZ;
ALTER TABLE analysis_jobs ADD COLUMN IF NOT EXISTS analysis_duration_seconds FLOAT;
"
```

---

## שלב 4: פתח את האתר

### 4.1 גש לממשק

פתח בדפדפן:
```
http://localhost:3000
```

### 4.2 התחבר

תתבקש להזין סיסמה - זו שהגדרת ב-`SITE_PASSWORD` (ברירת מחדל: `wallet123`)

---

## שלב 5: בדוק שהכל עובד

### 5.1 בדוק Backend API

```
http://localhost:8000/docs
```

צריך לראות Swagger UI עם כל ה-endpoints.

### 5.2 בדוק Admin Dashboard

1. עבור ל-`http://localhost:3000/admin`
2. לחץ "Update Sanctions Lists"
3. בדוק שה-update מתחיל (ייקח 1-2 דקות)

### 5.3 נסה ניתוח ארנק

1. צור קובץ CSV עם 2-3 ארנקים:

```csv
address,chain
0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb,ethereum
0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045,base
```

שמור כ-`test_wallets.csv`

2. העלה דרך הממשק:
   - בחר את הקובץ
   - שם פרויקט: "Test"
   - Submit

3. עקוב אחרי ההתקדמות:
   - תראה טיימר שעובד בזמן אמת! ⏱️
   - Progress bar
   - מספר ארנקים שעובדו

4. כשמסתיים - צפה בדוח

---

## פקודות שימושיות

### ניהול Containers

```bash
# עצור את כולם
docker-compose down

# עצור והסר volumes (מחיקת DB!)
docker-compose down -v

# הפעל מחדש שירות ספציפי
docker-compose restart api
docker-compose restart worker

# הפעל מחדש הכל
docker-compose restart

# הורד images מחדש ובנה
docker-compose pull
docker-compose up --build -d
```

### צפייה בלוגים

```bash
# כל הלוגים
docker-compose logs -f

# רק Backend
docker-compose logs -f api

# רק Worker (חשוב לדיבאג!)
docker-compose logs -f worker

# 100 שורות אחרונות
docker-compose logs --tail=100 worker
```

### ניהול Database

```bash
# התחבר ל-PostgreSQL
docker exec -it profiler-db-1 psql -U wallet_user -d wallet_intel

# בתוך psql:
\dt                          # רשימת טבלאות
\d analysis_jobs            # מבנה טבלה
SELECT * FROM analysis_jobs; # כל ה-jobs
\q                          # יציאה

# Backup
docker exec profiler-db-1 pg_dump -U wallet_user wallet_intel > backup.sql

# Restore
docker exec -i profiler-db-1 psql -U wallet_user wallet_intel < backup.sql
```

### ניהול Redis

```bash
# התחבר ל-Redis CLI
docker exec -it profiler-redis-1 redis-cli

# בתוך redis-cli:
KEYS *          # כל המפתחות
GET some_key    # קרא ערך
FLUSHALL        # מחק הכל (זהירות!)
```

### Worker Management

```bash
# הפעל worker נוסף (לטעינה גבוהה)
docker-compose up -d --scale worker=3

# חזור ל-worker אחד
docker-compose up -d --scale worker=1

# Worker לא מגיב? הפעל מחדש
docker-compose restart worker
```

---

## פתרון בעיות נפוצות

### בעיה 1: "Cannot connect to the Docker daemon"

**פתרון**: Docker Desktop לא רץ.
- Windows: פתח Docker Desktop מתפריט Start
- Linux: `sudo systemctl start docker`

### בעיה 2: "Port already in use"

**פתרון**: פורט תפוס (3000 או 8000).

```bash
# Windows - בדוק מה תופס את הפורט
netstat -ano | findstr :3000
netstat -ano | findstr :8000

# הרוג את התהליך (החלף PID)
taskkill /PID <process_id> /F

# או שנה port ב-docker-compose.yml:
# frontend:
#   ports:
#     - "3001:3000"  # במקום 3000:3000
```

### בעיה 3: Worker לא מעבד jobs

**בדוק**:
```bash
# לוגים של Worker
docker-compose logs -f worker

# ודא ש-Redis רץ
docker-compose ps redis

# הפעל worker מחדש
docker-compose restart worker
```

### בעיה 4: "RPC error 401 Unauthorized"

**פתרון**: מפתח Alchemy שגוי או לא מוגדר.
- בדוק ש-`ETHEREUM_RPC_URL` ב-`.env` מכיל מפתח תקין
- קבל מפתח חדש מ-[dashboard.alchemy.com](https://dashboard.alchemy.com)
- הפעל מחדש: `docker-compose restart api worker`

### בעיה 5: Database migration errors

**פתרון**: עמודות חסרות.

```bash
# הרץ migrations ידנית
docker exec -it profiler-db-1 psql -U wallet_user -d wallet_intel -c "
ALTER TABLE analysis_jobs ADD COLUMN IF NOT EXISTS started_at TIMESTAMPTZ;
ALTER TABLE analysis_jobs ADD COLUMN IF NOT EXISTS completed_at TIMESTAMPTZ;
ALTER TABLE analysis_jobs ADD COLUMN IF NOT EXISTS analysis_duration_seconds FLOAT;
"
```

### בעיה 6: Frontend לא נטען (white screen)

**פתרון**:
```bash
# בדוק לוגים
docker-compose logs frontend

# Rebuild frontend
docker-compose up --build -d frontend

# אם לא עוזר - נקה הכל
docker-compose down
docker-compose up --build -d
```

---

## עדכון לגרסה חדשה

```bash
# Pull changes מגיטהאב
git pull origin main

# Rebuild containers
docker-compose down
docker-compose up --build -d

# הרץ migrations אם יש
# (ראה בהודעת commit אם יש ALTER TABLE commands)
```

---

## ביצועים ו-Scaling

### אופטימיזציה למחשב חלש

אם המחשב איטי, הקטן resource limits ב-`docker-compose.yml`:

```yaml
services:
  api:
    deploy:
      resources:
        limits:
          cpus: '0.5'
          memory: 512M
```

### הגדלת מספר Workers

```bash
# עבור faster processing (דורש RAM)
docker-compose up -d --scale worker=3
```

---

## סיכום מהיר

```bash
# 1. התקן Docker Desktop
# 2. צור .env
cp .env.example .env
# ערוך .env עם RPC keys

# 3. הפעל
docker-compose up --build -d

# 4. הוסף עמודות DB
docker exec -it profiler-db-1 psql -U wallet_user -d wallet_intel -c "
ALTER TABLE analysis_jobs ADD COLUMN IF NOT EXISTS started_at TIMESTAMPTZ;
ALTER TABLE analysis_jobs ADD COLUMN IF NOT EXISTS completed_at TIMESTAMPTZ;
ALTER TABLE analysis_jobs ADD COLUMN IF NOT EXISTS analysis_duration_seconds FLOAT;
"

# 5. פתח בדפדפן
http://localhost:3000
```

**זהו! המערכת רצה מקומית על המחשב שלך 🎉**

---

## עזרה נוספת

- **Documentation**: [README.md](README.md)
- **Deployment**: [DEPLOYMENT.md](DEPLOYMENT.md)
- **System Docs**: [SYSTEM_DOCUMENTATION.md](SYSTEM_DOCUMENTATION.md)
- **GitHub Issues**: פתח issue בריפו
