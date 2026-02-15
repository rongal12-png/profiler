# Wallet Intelligence - מערכת ניתוח ארנקים קריפטו

מערכת מתקדמת לניתוח והערכת ארנקי קריפטו עבור פרויקטים ו-Launchpads.

## 🚀 תכונות

- ✅ ניתוח multi-chain (Ethereum, Base, Arbitrum, Polygon, Solana ועוד)
- ✅ מערכת ציון מתקדמת (Whale/Tuna/Fish)
- ✅ זיהוי 10 פרסונות משתמשים (Trader, Staker, Farmer, וכו')
- ✅ בדיקת sanctions (OFAC, EU, Israel NBCTF)
- ✅ Token Intelligence - זיהוי סוגי טוקנים
- ✅ Community Quality Score
- ✅ דוחות PDF/DOCX/CSV/JSON
- ✅ ממשק ניהול Admin עם הגדרות ניתנות להתאמה
- ✅ הגנת סיסמה לאתר

## 📋 דרישות מקדימות

- Docker & Docker Compose
- חשבון RPC (Alchemy / Infura / QuickNode)

## ⚙️ התקנה מקומית

1. שכפל את הפרויקט:
```bash
git clone https://github.com/YOUR_USERNAME/profiler.git
cd profiler
```

2. צור קובץ `.env` מתוך `.env.example`:
```bash
cp .env.example .env
```

3. ערוך את `.env` והגדר:
   - `POSTGRES_PASSWORD` - סיסמת מסד נתונים
   - `ETHEREUM_RPC_URL`, `BASE_RPC_URL`, וכו' - נקודות קצה של RPC
   - `ADMIN_API_KEY` - מפתח API לניהול
   - `SITE_PASSWORD` - סיסמה לגישה לאתר

4. הרם את המערכת:
```bash
docker-compose up -d --build
```

5. פתח בדפדפן:
```
http://localhost:3000
```

## 🌍 העלאה לאינטרנט

### אופציה 1: Railway.app (מומלץ - חינם להתחלה)

1. צור חשבון ב-[Railway.app](https://railway.app)

2. חבר את הריפו מגיטהאב

3. הוסף שירותים:
   - **PostgreSQL** (Add Service → Database → PostgreSQL)
   - **Redis** (Add Service → Database → Redis)
   - **Backend** (Add Service → GitHub Repo)
   - **Worker** (Add Service → GitHub Repo - same repo, different start command)
   - **Frontend** (Add Service → GitHub Repo - same repo, different root directory)

4. הגדר משתני סביבה עבור כל שירות (העתק מה-.env)

5. הגדר start commands:
   - Backend: `cd app && uvicorn api.main:app --host 0.0.0.0 --port $PORT`
   - Worker: `cd app && celery -A worker worker --loglevel=info`
   - Frontend: יזוהה אוטומטית מ-package.json

### אופציה 2: Render.com

1. צור חשבון ב-[Render.com](https://render.com)

2. צור Blueprint מ-`render.yaml` (ראה למטה)

3. חבר את הריפו והוסף משתני סביבה

### אופציה 3: DigitalOcean App Platform

1. צור Droplet או App Platform
2. העלה באמצעות Docker Compose
3. הגדר DNS והפנייה

## 🔐 אבטחה

- **סיסמת אתר**: מוגדרת ב-`SITE_PASSWORD` - משתנה את זה לסיסמה חזקה
- **Admin API**: מוגדר ב-`ADMIN_API_KEY` - רק לשימוש בקריאות API
- **PostgreSQL**: אל תחשוף את הפורט החוצה
- **Redis**: אל תחשוף את הפורט החוצה

## 📊 שימוש

1. התחבר עם הסיסמה שהגדרת
2. העלה קובץ CSV עם רשימת ארנקים (עמודות: address, chain)
3. המתן לניתוח (תלוי במספר הארנקים)
4. צפה בדוחות והורד קבצים

## 🛠️ פיתוח

```bash
# Backend
cd app
pip install -r requirements.txt
uvicorn api.main:app --reload

# Frontend
cd frontend
npm install
npm run dev

# Worker
cd app
celery -A worker worker --loglevel=info
```

## 📝 רישיון

MIT License

## 🤝 תמיכה

פתח issue בגיטהאב לתמיכה או שאלות.
