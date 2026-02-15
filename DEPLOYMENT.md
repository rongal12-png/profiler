# 🚀 מדריך פריסה מלא - Wallet Intelligence

## שלב 1: העלאה לגיטהאב

### 1.1 צור repository חדש בגיטהאב

1. עבור ל-[GitHub](https://github.com) והתחבר
2. לחץ על "New repository" (או הכנס ל-https://github.com/new)
3. מלא פרטים:
   - **Repository name**: `wallet-intelligence` (או כל שם אחר)
   - **Description**: "Advanced blockchain wallet analysis system"
   - **Private/Public**: בחר לפי העדפה (מומלץ Private אם יש נתונים רגישים)
   - **DON'T** initialize with README/gitignore (יש לנו כבר)

4. לחץ "Create repository"

### 1.2 חבר את הקוד המקומי לגיטהאב

בטרמינל, הרץ:

```bash
cd "C:\Users\steve\Documents\Profiler"

# החלף USERNAME ו-REPOSITORY בפרטים שלך
git remote add origin https://github.com/USERNAME/REPOSITORY.git

# דחוף לגיטהאב
git branch -M main
git push -u origin main
```

אם תתבקש להזין פרטי התחברות:
- Username: שם המשתמש שלך בגיטהאב
- Password: **לא** הסיסמה הרגילה! צריך **Personal Access Token**

#### יצירת Personal Access Token:
1. עבור ל-GitHub → Settings → Developer settings → Personal access tokens → Tokens (classic)
2. "Generate new token (classic)"
3. תן שם (למשל "Wallet Intelligence Deploy")
4. בחר scopes: `repo` (full control)
5. Generate token ושמור אותו במקום בטוח

---

## שלב 2: פריסה ל-Railway.app (הכי פשוט - מומלץ!)

### למה Railway?
- ✅ תהליך פריסה פשוט ומהיר
- ✅ תקופת ניסיון חינמית ($5 קרדיט חודשי)
- ✅ תמיכה ב-Docker Compose
- ✅ PostgreSQL + Redis מובנים
- ✅ SSL אוטומטי
- ✅ עדכונים אוטומטיים מגיטהאב

### שלב 2.1: הגדרת Railway

1. **צור חשבון**:
   - עבור ל-[Railway.app](https://railway.app)
   - Sign up with GitHub (יחבר אוטומטית את הריפוזיטורי)

2. **צור פרויקט חדש**:
   - לחץ "New Project"
   - בחר "Deploy from GitHub repo"
   - חפש את `wallet-intelligence` (או השם שנתת)
   - לחץ על הריפו

### שלב 2.2: הוסף שירותים

Railway יזהה את `docker-compose.yml` אוטומטית. אבל אנחנו נעשה את זה באופן ידני:

#### 2.2.1 PostgreSQL
1. לחץ "+ New" → "Database" → "Add PostgreSQL"
2. שמור את הפרטים שמופיעים (Railway מגדיר אוטומטית)

#### 2.2.2 Redis
1. לחץ "+ New" → "Database" → "Add Redis"
2. שמור את הפרטים

#### 2.2.3 Backend API
1. לחץ "+ New" → "GitHub Repo" → בחר את הריפו שלך
2. הגדרות:
   - **Root Directory**: `/` (כברירת מחדל)
   - **Build Command**: (השאר ריק - Docker יטפל)
   - **Start Command**: `uvicorn api.main:app --host 0.0.0.0 --port $PORT`
3. **Variables** (Environment):
   ```
   DATABASE_URL = (העתק מהשירות PostgreSQL)
   REDIS_URL = (העתק מהשירות Redis)
   ETHEREUM_RPC_URL = https://eth-mainnet.g.alchemy.com/v2/YOUR_ALCHEMY_KEY
   BASE_RPC_URL = https://base-mainnet.g.alchemy.com/v2/YOUR_ALCHEMY_KEY
   ARBITRUM_RPC_URL = https://arb-mainnet.g.alchemy.com/v2/YOUR_ALCHEMY_KEY
   POLYGON_RPC_URL = https://polygon-mainnet.g.alchemy.com/v2/YOUR_ALCHEMY_KEY
   SOLANA_RPC_URL = https://api.mainnet-beta.solana.com
   ADMIN_API_KEY = [סיסמה חזקה שתבחר]
   COINGECKO_API_KEY = [אופציונלי]
   ```

#### 2.2.4 Celery Worker
1. לחץ "+ New" → "GitHub Repo" → אותו ריפו
2. הגדרות:
   - **Start Command**: `celery -A worker worker --loglevel=info`
3. **Variables**: אותם משתנים כמו ב-Backend (העתק מ-Backend API)

#### 2.2.5 Celery Beat
1. לחץ "+ New" → "GitHub Repo" → אותו ריפו
2. הגדרות:
   - **Start Command**: `celery -A worker beat --loglevel=info`
3. **Variables**: אותם משתנים

#### 2.2.6 Frontend
1. לחץ "+ New" → "GitHub Repo" → אותו ריפו
2. הגדרות:
   - **Root Directory**: `/frontend`
   - **Build Command**: `npm install && npm run build`
   - **Start Command**: `npm start`
3. **Variables**:
   ```
   NODE_ENV = production
   NEXT_PUBLIC_API_URL = [כתובת ה-Backend API service - תקבל מRailway]
   SITE_PASSWORD = [הסיסמה שרוצים לאתר]
   ```

### שלב 2.3: הגדר Networking

1. עבור לשירות **Frontend**
2. Settings → Networking → Generate Domain
3. שמור את ה-URL (למשל `wallet-intelligence.up.railway.app`)

4. עבור לשירות **Backend API**
5. Settings → Networking → Generate Domain
6. העתק את ה-URL
7. חזור ל-**Frontend** → Variables → עדכן את `NEXT_PUBLIC_API_URL`

### שלב 2.4: Deploy!

Railway יתחיל לבנות ולפרוס אוטומטית. אפשר לראות logs:
- לחץ על כל שירות → Deployments → לחץ על הפריסה האחרונה → View Logs

**זמן פריסה**: 5-10 דקות

### שלב 2.5: בדיקה

1. פתח את ה-URL של ה-Frontend
2. תתבקש להזין סיסמה (זו שהגדרת ב-`SITE_PASSWORD`)
3. העלה קובץ CSV עם ארנקים
4. בדוק שהניתוח עובד

---

## שלב 3: פריסה ל-Render.com (אלטרנטיבה)

### למה Render?
- ✅ תקופת ניסיון חינמית
- ✅ קל לתחזוקה
- ✅ Blueprint deployment (קובץ קונפיג אחד)

### שלבי הפריסה:

1. **צור חשבון ב-[Render.com](https://render.com)**
   - Sign up with GitHub

2. **צור Blueprint**:
   - Dashboard → Blueprints → New Blueprint Instance
   - Connect Repository → בחר `wallet-intelligence`
   - Render יזהה את `render.yaml` אוטומטית

3. **הגדר משתנים**:
   הכנס משתנים דומים לאלו של Railway

4. **Deploy**:
   לחץ "Apply" - Render יעלה הכל אוטומטית

---

## שלב 4: RPC Endpoints (חובה!)

המערכת צריכה גישה ל-blockchain. בחר אחד מהאפשרויות:

### אופציה 1: Alchemy (מומלץ)
1. עבור ל-[Alchemy.com](https://www.alchemy.com/)
2. צור חשבון חינמי
3. Create App:
   - **Chain**: Ethereum Mainnet
   - **Network**: Mainnet
4. העתק את ה-HTTPS URL
5. חזור על זה עבור Base, Arbitrum, Polygon

**Free Tier**: 300M compute units/month (מספיק לכמה אלפי ארנקים ביום)

### אופציה 2: Infura
1. עבור ל-[Infura.io](https://infura.io)
2. צור פרויקט
3. קבל API key
4. URLs: `https://mainnet.infura.io/v3/YOUR_API_KEY`

### אופציה 3: QuickNode
1. עבור ל-[QuickNode.com](https://www.quicknode.com/)
2. צור endpoint
3. בחר chains

---

## שלב 5: הגדרות אבטחה

### 5.1 שנה סיסמאות ברירת מחדל

ב-Railway/Render Variables, ודא שהגדרת:
```
SITE_PASSWORD = [סיסמה חזקה - לא "wallet123"!]
ADMIN_API_KEY = [מחרוזת אקראית ארוכה]
POSTGRES_PASSWORD = [יצר אוטומטית ע"י Railway/Render - טוב]
```

### 5.2 HTTPS בלבד
Railway ו-Render מספקים SSL אוטומטית - אל תשתמש ב-HTTP.

### 5.3 הגבל גישה ל-Admin
Admin endpoints ב-`/admin/*` דורשים X-API-Key header. זה טוב.

### 5.4 Rate Limiting (אופציונלי)
אפשר להוסיף Cloudflare לפני האתר למניעת злоупотреблением.

---

## שלב 6: תחזוקה ועדכונים

### עדכון הקוד

כשעורכים משהו בקוד:
```bash
git add .
git commit -m "תיאור השינוי"
git push origin main
```

Railway/Render יזהו את השינוי ויפרסו אוטומטית מחדש! 🎉

### ניטור

**Railway**:
- Logs → ראה לוגים בזמן אמת
- Metrics → CPU/RAM usage

**Render**:
- Events → Deploy history
- Logs → Runtime logs

### Backup

**PostgreSQL**:
- Railway: Settings → Data → Backups (אוטומטי)
- Render: Settings → Backups (manual/scheduled)

---

## שלב 7: בעיות נפוצות

### בעיה: "Cannot connect to database"
**פתרון**: בדוק ש-`DATABASE_URL` מוגדר נכון. Railway/Render צריכים לספק את זה אוטומטית.

### בעיה: "RPC error: 429 Too Many Requests"
**פתרון**: עברת על ה-rate limit של Alchemy/Infura. שדרג לתוכנית בתשלום או השתמש במספר API keys.

### בעיה: Frontend לא מתחבר ל-Backend
**פתרון**: בדוק ש-`NEXT_PUBLIC_API_URL` מצביע לכתובת הנכונה של ה-Backend API.

### בעיה: Worker לא מעבד jobs
**פתרון**: בדוק ש-Celery Worker רץ. ב-Railway: Services → Worker → Logs.

---

## שלב 8: שיפורים נוספים (אופציונלי)

### 8.1 Custom Domain
במקום `wallet-intelligence.up.railway.app`:
1. קנה דומיין (Namecheap, GoDaddy, Cloudflare)
2. Railway: Settings → Custom Domain → הוסף
3. עדכן DNS records לפי ההוראות

### 8.2 Cloudflare CDN
1. העבר את הדומיין ל-Cloudflare
2. הפעל Proxy (☁️ icon)
3. תקבל: DDoS protection, caching, rate limiting

### 8.3 Monitoring עם Sentry
1. צור חשבון ב-[Sentry.io](https://sentry.io)
2. הוסף Sentry SDK לקוד
3. קבל התראות על שגיאות

---

## 📞 תמיכה

אם נתקעת:
1. בדוק את ה-Logs בשירות הרלוונטי
2. פתח issue בגיטהאב
3. Railway Discord: https://discord.gg/railway
4. Render Community: https://community.render.com

---

## ✅ Checklist לפני Go-Live

- [ ] כל משתני הסביבה מוגדרים
- [ ] סיסמאות שונו מברירת מחדל
- [ ] RPC endpoints עובדים (בדקת בלוג)
- [ ] PostgreSQL + Redis רצים
- [ ] Backend API עונה (GET /docs)
- [ ] Frontend נטען ומציג login page
- [ ] Worker מעבד jobs (נסה להעלות CSV קטן)
- [ ] Sanctions update עובד (Admin → Sanctions → Update)
- [ ] PDF/DOCX export עובדים

**בהצלחה! 🚀**
