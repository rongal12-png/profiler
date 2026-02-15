# Wallet Intelligence System - תיעוד מקיף

## תוכן עניינים
1. [מה המערכת בודקת?](#מה-המערכת-בודקת)
2. [מערכת הציונים](#מערכת-הציונים)
3. [סיווג רמות (Tiers)](#סיווג-רמות-tiers)
4. [סוגי ארנקים (Wallet Types)](#סוגי-ארנקים-wallet-types)
5. [פרסונות משתמשים (Personas)](#פרסונות-משתמשים-personas)
6. [ניקוד קהילה (Community Score)](#ניקוד-קהילה-community-score)
7. [אינטליגנציה על אחזקות (Token Intelligence)](#אינטליגנציה-על-אחזקות-token-intelligence)
8. [אותות כוונות השקעה (Investment Intent)](#אותות-כוונות-השקעה-investment-intent)
9. [הסבר על עמודות ה-CSV/Excel](#הסבר-על-עמודות-הcsvexcel)
10. [בדיקות סנקציות](#בדיקות-סנקציות)
11. [דגלי סיכון](#דגלי-סיכון)

---

## מה המערכת בודקת?

המערכת מנתחת רשימת ארנקי קריפטו ומספקת **אינטליגנציה ברמת הקהילה והפרט** עבור פרוייקטים בלוקצ'יין.

### תהליך הניתוח:
1. **קריאת נתוני בלוקצ'יין** - יתרות, מספר עסקאות, טוקנים
2. **זיהוי זהות** - האם זה משתמש, בורסה, חוזה חכם, גשר?
3. **ניקוד רב-ממדי** - 5 מרכיבי ציון עם משקלות
4. **סיווג לרמות ופרסונות** - Whale, Tuna, Fish, DeFi Native, Newcomer, וכו'
5. **אנליזת אחזקות** - סיווג טוקנים (native, stablecoin, staked, governance)
6. **זיהוי כוונות השקעה** - dry powder, long-term commitment, readiness
7. **ציון קהילה** - ציון מצטבר 0-100 עם ציון A+ עד F
8. **בדיקת סנקציות** - מול OFAC, EU, Israel NBCTF
9. **דגלי בריאות ורסקון** - אזהרות אדומות/צהובות/ירוקות

---

## מערכת הציונים

כל ארנק מקבל **ציון משקיע (Investor Score)** בטווח 0-100, המחושב מ-5 מרכיבים:

### 1. **Balance Score** (משקל: 30%)
מודד את סך הנכסים בארנק (native + stablecoins + tokens).

**חישוב:**
- `$0-$100`: 0-20 נקודות
- `$100-$1,000`: 20-40 נקודות
- `$1,000-$10,000`: 40-60 נקודות
- `$10,000-$100,000`: 60-80 נקודות
- `$100,000+`: 80-100 נקודות

**לוגריתמי**: `score = min(100, 20 * log10(max(1, net_worth_usd)))`

---

### 2. **Activity Score** (משקל: 15%)
מודד את רמת הפעילות לפי מספר עסקאות.

**חישוב:**
- `0-10 tx`: 0-20 נקודות
- `10-50 tx`: 20-40 נקודות
- `50-200 tx`: 40-60 נקודות
- `200-1000 tx`: 60-80 נקודות
- `1000+ tx`: 80-100 נקודות

**לוגריתמי**: `score = min(100, 25 * log10(max(1, tx_count)))`

---

### 3. **DeFi Investor Score** (משקל: 25%)
מודד מעורבות ב-DeFi לפי מגוון הטוקנים.

**חישוב:**
- `0-1 tokens`: 0-20 נקודות
- `2-3 tokens`: 20-40 נקודות
- `4-6 tokens`: 40-60 נקודות
- `7-10 tokens`: 60-80 נקודות
- `10+ tokens`: 80-100 נקודות

**לוגריתמי**: `score = min(100, 33 * log10(max(1, token_count)))`

---

### 4. **Reputation Score** (משקל: 20%)
מבוסס על תוויות ידועות (labels) וסוג הישות.

**ציונים:**
- **VC / KOL / Protocol**: 90-100 נקודות
- **DEX Router / Bridge**: 70 נקודות
- **CEX Exchange**: 60 נקודות
- **High Activity** (1000+ tx): 75 נקודות
- **Inactive Holder**: 40 נקודות
- **Smart Contract**: 30 נקודות
- **Unknown User**: 50 נקודות (ברירת מחדל)

---

### 5. **Sybil Risk Score** (משקל: -10%, **מפחית**)
מזהה ארנקים חשודים כ-Sybil/Farming.

**אינדיקטורים:**
- יתרה נמוכה + פעילות גבוהה → סיכון גבוה
- `net_worth < $100` AND `tx_count > 50` → 60-80 נקודות
- `net_worth < $10` → 90 נקודות
- דגל תשומת לב: ציון sybil ≥ 40

**חישוב:**
```python
if net_worth_usd < 100 and tx_count > 50:
    sybil_risk = min(100, 50 + (tx_count / 10))
elif net_worth_usd < 10:
    sybil_risk = 90
else:
    sybil_risk = 0
```

---

### **Investor Score הכולל**

```
Investor Score = (Balance × 0.30) + (Activity × 0.15) + (DeFi × 0.25)
                 + (Reputation × 0.20) + (Sybil × -0.10)
```

**טווח:** 0-100 (נעגל ל-1 ספרה אחרי הנקודה)

**דוגמה:**
- Balance: 75 (10K$)
- Activity: 60 (150 tx)
- DeFi: 55 (5 tokens)
- Reputation: 50 (unknown)
- Sybil: -5 (ציון sybil 50)

```
Score = (75×0.3) + (60×0.15) + (55×0.25) + (50×0.2) + (50×-0.1)
      = 22.5 + 9 + 13.75 + 10 - 5
      = 50.25
```

---

## סיווג רמות (Tiers)

לאחר חישוב ה-Investor Score, הארנקים מסווגים לרמות:

### **Whale** 🐋
- **תנאי:** Investor Score ≥ 55
- **ברירת מחדל:** 55 (ניתן לשינוי בהגדרות Admin)
- **משמעות:** משקיעים גדולים עם נכסים משמעותיים ופעילות DeFi
- **דוגמה:** $100K+, 200+ tx, 7+ tokens

### **Tuna** 🐟
- **תנאי:** 30 ≤ Investor Score < 55
- **ברירת מחדל:** 30-54
- **משמעות:** משקיעים בינוניים, פעילים סביר, אחזקות מתונות
- **דוגמה:** $5K-$50K, 50-200 tx, 3-6 tokens

### **Fish** 🐠
- **תנאי:** Investor Score < 30
- **משמעות:** משקיעים קטנים, משתמשים חדשים, או ארנקי dust
- **דוגמה:** $100-$1K, 10-50 tx, 1-2 tokens

### **Infra** ⚙️
- **תנאי מיוחד:** סוג ארנק הוא `CEX_EXCHANGE`, `DEX_ROUTER`, `BRIDGE`, `PROTOCOL`, או `CONTRACT`
- **משמעות:** לא משתמש אמיתי, אלא תשתית (לא נכנס לחישוב מדדי קהילה)

**הערה:** סף Whale ו-Tuna ניתנים להגדרה ב-Admin Dashboard → Scoring Settings.

---

## סוגי ארנקים (Wallet Types)

המערכת מזהה 7 סוגי ארנקים לפי 3 שכבות:

### שכבה A: תוויות ידועות (JSON)
**קובץ:** `app/data/known_labels.json`

סוגים:
- **CEX_EXCHANGE**: בורסות מרכזיות (Binance, Coinbase, Kraken, וכו')
- **DEX_ROUTER**: נתבי DEX (Uniswap Router, SushiSwap Router)
- **BRIDGE**: גשרים בין-רשתות (Across, Hop Protocol)
- **PROTOCOL**: חוזי פרוטוקולים (Aave Pool, Compound)
- **VC**: קרנות הון סיכון
- **KOL**: מנהיגי דעה (Vitalik, influencers)

### שכבה B: זיהוי חוזה חכם
אם `w3.eth.get_code(address) != "0x"` → **CONTRACT**

### שכבה C: היוריסטיקה
- פעילות גבוהה מאוד (5000+ tx) + אין קוד → **DEX_ROUTER** חשוד
- אחרת → **USER**

**סדר עדיפויות:** A > B > C

---

## פרסונות משתמשים (Personas)

כל ארנק מקבל **פרסונה** המתארת את התנהגותו, עם **רמת ביטחון** (confidence 0-0.95) ורשימת **ראיות** (evidence).

### **1. Whale Investor** 🐋
- **תנאי:** Investor Score ≥ 70 AND net_worth ≥ $100,000
- **Confidence:** 0.95
- **Evidence:**
  - "Very high net worth ($XXX,XXX+)"
  - "Strong DeFi engagement"
  - "Established reputation"

---

### **2. DeFi Native** 🦾
- **תנאי:** DeFi Score ≥ 60 AND token_diversity ≥ 5
- **Confidence:** 0.85
- **Evidence:**
  - "High DeFi investor score (XX)"
  - "Holds X+ different tokens"
  - "Active across protocols"

---

### **3. Staker** 🔒
- **תנאי:** staked_share > 0.3 (30%+ מהנכסים הם staked tokens)
- **Confidence:** 0.80
- **Evidence:**
  - "XX% of portfolio in staked assets"
  - "Long-term commitment signal"
  - (אם יש governance tokens) "Also holds governance tokens"

**Staked Tokens:** stETH, rETH, cbETH, wstETH, stMATIC, mSOL, JitoSOL

---

### **4. Governance Participant** 🗳️
- **תנאי:** has_governance_tokens = True
- **Confidence:** 0.75
- **Evidence:**
  - "Holds governance tokens (UNI/AAVE/LDO/MKR)"
  - "Protocol engagement signal"

**Governance Tokens:** UNI, AAVE, LDO, MKR, ARB, OP, JTO

---

### **5. Active Trader** 📊
- **תנאי:** tx_count ≥ 200 AND Activity Score ≥ 60
- **Confidence:** 0.70
- **Evidence:**
  - "XXX+ transactions"
  - "High on-chain activity"

---

### **6. Stablecoin Holder** 💵
- **תנאי:** stable_usd > 0.6 × net_worth (60%+ בstablecoins)
- **Confidence:** 0.65
- **Evidence:**
  - "XX% portfolio in stablecoins"
  - "Dry powder for deployment"

---

### **7. Newcomer** 🆕
- **תנאי:** tx_count ≤ 5 AND net_worth < $1,000
- **Confidence:** 0.60
- **Evidence:**
  - "Low transaction count (X)"
  - "Small portfolio ($XXX)"
  - "Early-stage user"

---

### **8. Sybil / Farmer** 🚜
- **תנאי:** sybil_risk_score ≥ 60
- **Confidence:** 0.80
- **Evidence:**
  - "Low value + high activity pattern"
  - "Sybil risk score: XX"

---

### **9. Passive Investor** 💤
- **תנאי:** tx_count < 20 AND net_worth ≥ $5,000
- **Confidence:** 0.55
- **Evidence:**
  - "Low activity (XX tx)"
  - "Moderate holdings ($X,XXX)"

---

### **10. Casual User** 👤
- **תנאי:** ברירת מחדל (לא מתאים לקטגוריות אחרות)
- **Confidence:** 0.50
- **Evidence:**
  - "Standard user profile"
  - "No strong signals"

---

### דוגמה לפלט Persona Detail:
```json
{
  "primary": "DeFi Native",
  "confidence": 0.85,
  "evidence": [
    "High DeFi investor score (68)",
    "Holds 7 different tokens",
    "Active across protocols"
  ],
  "secondary": "Active Trader"
}
```

---

## ניקוד קהילה (Community Score)

**Community Quality Score** הוא ציון ברמת הפרויקט (0-100) עם ציון אות (A+ עד F).

### מרכיבי הציון (5):

#### **1. User Ratio** (משקל: 30%)
אחוז הארנקים שהם **משתמשים אמיתיים** (לא תשתית).

**חישוב:**
```
user_ratio = user_count / total_wallets
user_ratio_score = min(100, user_ratio × 100 / 0.7)
```

**ציון מושלם:** 70%+ users
- 70%+ → 100 נקודות
- 50% → 71 נקודות
- 30% → 43 נקודות

---

#### **2. Investor Quality** (משקל: 25%)
ממוצע ה-Investor Score של המשתמשים.

**חישוב:**
```
investor_quality = avg(investor_score) למשתמשים בלבד
```

**טווח:** 0-100 (ישיר)

---

#### **3. Diversity** (משקל: 15%)
אנטרופיית שנון (Shannon Entropy) של התפלגות הפרסונות.

**חישוב:**
```
entropy = -Σ(p_i × log₂(p_i))
diversity_score = (entropy / max_entropy) × 100
```

**ציון גבוה:** פרסונות מגוונות (DeFi Native, Traders, Whales, וכו')
**ציון נמוך:** כולם באותה קטגוריה (למשל, כולם Casual Users)

---

#### **4. Whale Presence** (משקל: 15%)
אחוז ה-Whales מסך הארנקים.

**חישוב:**
```
whale_pct = whale_count / total_wallets

if 0.05 ≤ whale_pct ≤ 0.15:  # sweet spot: 5-15%
    whale_score = 100
elif whale_pct < 0.05:
    whale_score = (whale_pct / 0.05) × 100
else:  # too whale-heavy
    whale_score = max(100 - (whale_pct - 0.15) × 300, 20)
```

**אידיאלי:** 5-15% Whales
- פחות מ-5% → מדרגתי (0% → 0 נקודות, 5% → 100)
- 5-15% → 100 נקודות
- מעל 15% → קנס (20% → 85 נקודות)

---

#### **5. Health Signals** (משקל: 15%)
היפוך של סיכוני Sybil וסנקציות.

**חישוב:**
```
sybil_ratio = sybil_count / total_wallets
sanctions_ratio = sanctions_count / total_wallets
health_score = max(0, 100 - sybil_ratio × 200 - sanctions_ratio × 500)
```

**משמעות:**
- 0% sybil + 0% sanctions → 100 נקודות
- 20% sybil → 60 נקודות
- 1% sanctions → 0 נקודות (חמור מאוד)

---

### **Community Score הכולל**

```
Community Score = (user_ratio × 0.30) + (investor_quality × 0.25)
                  + (diversity × 0.15) + (whale_presence × 0.15)
                  + (health × 0.15)
```

**טווח:** 0-100 (נעגל ל-1 ספרה)

---

### **מיפוי לציוני אות**

| ציון | Grade | משמעות |
|------|-------|--------|
| 90-100 | **A+** | קהילה מצוינת - מגוונת, איכותית, בריאה |
| 85-89 | **A** | קהילה טובה מאוד |
| 80-84 | **A-** | קהילה טובה |
| 75-79 | **B+** | קהילה מעל לממוצע |
| 70-74 | **B** | קהילה ממוצעת-טובה |
| 65-69 | **B-** | קהילה ממוצעת |
| 60-64 | **C+** | קהילה מתחת לממוצע |
| 55-59 | **C** | קהילה חלשה |
| 50-54 | **C-** | קהילה חלשה מאוד |
| 40-49 | **D** | קהילה בעייתית |
| 0-39 | **F** | קהילה נכשלת |

---

### **Narrative (טקסט הסבר)**

דוגמה:
> "This community scores 78.5/100 (Grade B+), indicating a healthy and engaged wallet base. Average investor quality is strong — experienced DeFi participants are well-represented."

---

## אינטליגנציה על אחזקות (Token Intelligence)

המערכת מסווגת את כל האחזקות ל-5 קטגוריות:

### **1. Native** (מטבע הרשת)
- ETH, SOL, MATIC, ARB, BASE

### **2. Stablecoin** 💵
- USDC, USDT, DAI, BUSD, FRAX

### **3. Staked** 🔒
- stETH, rETH, cbETH, wstETH, stMATIC, mSOL, JitoSOL
- **תמחור:** מחיר הנכס הבסיסי (stETH ≈ ETH)

### **4. Governance** 🗳️
- UNI, AAVE, LDO, MKR, ARB, OP, JTO
- **תמחור:** $0 (הספירה חשובה יותר מהערך)

### **5. Other** (טוקנים אחרים)
- כל שאר הטוקנים (DeFi tokens, memecoins, NFTs)

---

### **מדדי ריכוז**

#### **HHI (Herfindahl-Hirschman Index)**
מדד ריכוז סטנדרטי:
```
HHI = Σ(share_i²)
```

**פרשנות:**
- **0.0-0.15:** מגוון מאוד (Diversified)
- **0.15-0.25:** מגוון בינוני (Moderate)
- **0.25-1.0:** מרוכז (Concentrated)

---

#### **Stablecoin Share**
```
stablecoin_share = stablecoin_usd / total_usd
```

**משמעות:**
- **>60%:** Dry powder (כסף מוכן להשקעה)
- **30-60%:** ניהול סיכון
- **<30%:** full exposure

---

#### **Staked Share**
```
staked_share = staked_usd / total_usd
```

**משמעות:**
- **>30%:** Staker persona
- **Long-term commitment** signal

---

### **אותות (Signals)**

- **dry_powder_signal:** stablecoin_share > 0.5
- **long_term_signal:** staked_share > 0.2 OR token_diversity ≥ 5

---

## אותות כוונות השקעה (Investment Intent)

המערכת מזהה 6 אותות:

### **1. Dry Powder** 💵
- **תנאי:** stablecoin_share > 0.5
- **Strength:** strong (>75%), moderate (50-75%), weak (<50%)
- **Detail:** "XX% portfolio in stablecoins, ready to deploy"

### **2. Long-Term Commitment** 🔒
- **תנאי:** staked_share > 0.2 OR token_diversity ≥ 7
- **Strength:** strong (staked >40%), moderate (staked 20-40%), weak (diversity only)
- **Detail:** "XX% staked, diverse holdings"

### **3. Governance Participant** 🗳️
- **תנאי:** has_governance_tokens = True
- **Strength:** strong (Whale), moderate (Tuna), weak (Fish)
- **Detail:** "Holds governance tokens (UNI/AAVE/etc)"

### **4. Diversified Portfolio** 📊
- **תנאי:** token_diversity ≥ 5 AND concentration < 0.5
- **Strength:** strong (10+ tokens), moderate (7-9), weak (5-6)
- **Detail:** "Holds X tokens, low concentration (HHI: X.XX)"

### **5. Concentrated Position** 🎯
- **תנאי:** concentration > 0.7
- **Strength:** strong (>0.9), moderate (0.7-0.9)
- **Detail:** "XX% in single asset, high conviction"

### **6. Active Trader** 📈
- **תנאי:** tx_count > 200 AND Activity Score > 60
- **Strength:** strong (500+ tx), moderate (200-500)
- **Detail:** "XXX transactions, frequent on-chain activity"

---

### **Investment Readiness**

סיכום רמת המוכנות להשקעה:

- **High:** 3+ strong signals, או dry_powder + long_term
- **Medium:** 1-2 signals, או mix של moderate
- **Low:** אין אותות משמעותיים

---

### **Estimated Deployable USD**

```
if dry_powder_signal:
    deployable = stablecoin_usd × 0.8  # 80% deployment assumption
else:
    deployable = 0
```

---

## הסבר על עמודות ה-CSV/Excel

### קובץ הקלט (Input CSV)
**נדרש 2 עמודות:**

| עמודה | הסבר | דוגמה |
|-------|------|-------|
| `address` | כתובת הארנק | `0x73BCEb1Cd57C711f2AB7f80E...` |
| `chain` | שם הרשת | `ethereum`, `base`, `arbitrum`, `polygon`, `solana` |

**רשתות נתמכות:**
- `ethereum`
- `base`
- `arbitrum`
- `polygon`
- `solana`

---

### קובץ הפלט (Output CSV)

הדוח מכיל **33+ עמודות**:

#### **זיהוי בסיסי**
| עמודה | הסבר | דוגמה |
|-------|------|-------|
| `address` | כתובת הארנק | `0xabc...` |
| `chain` | הרשת | `ethereum` |
| `tier` | רמה | `Whale`, `Tuna`, `Fish`, `Infra` |
| `wallet_type` | סוג ארנק | `USER`, `CEX_EXCHANGE`, `DEX_ROUTER`, וכו' |
| `persona` | פרסונה עיקרית | `DeFi Native`, `Whale Investor`, וכו' |

---

#### **נכסים ויתרות**
| עמודה | הסבר | טווח |
|-------|------|------|
| `native_balance` | יתרת מטבע מקומי (ETH/SOL) | 0+ |
| `est_net_worth_usd` | הערכת שווי כולל ב-USD | $0+ |
| `stable_usd_total` | סך stablecoins ב-USD | $0+ |

---

#### **ציוני משקיע**
| עמודה | הסבר | טווח |
|-------|------|------|
| `investor_score` | ציון משקיע כולל | 0-100 |
| `balance_score` | ציון יתרה | 0-100 |
| `activity_score` | ציון פעילות | 0-100 |
| `defi_investor_score` | ציון DeFi | 0-100 |
| `reputation_score` | ציון מוניטין | 0-100 |
| `sybil_risk_score` | ציון סיכון Sybil | 0-100 |
| `product_relevance_score` | רלוונטיות למוצר | 0-100 |

---

#### **פעילות**
| עמודה | הסבר | טווח |
|-------|------|------|
| `tx_count` | מספר עסקאות | 0+ |
| `is_contract` | האם חוזה חכם | `true` / `false` |
| `known_entity_type` | סוג ישות ידועה | `user`, `vc`, `kol`, וכו' |
| `labels_str` | תוויות | `Uniswap Router`, `Binance Hot Wallet` |

---

#### **אינטליגנציה מתקדמת (JSON)**
| עמודה | הסבר | מבנה |
|-------|------|------|
| `token_intelligence` | אנליזת אחזקות | `{"categories": {...}, "concentration": 0.3, ...}` |
| `persona_detail` | פרסונה מפורטת | `{"primary": "DeFi Native", "confidence": 0.85, "evidence": [...]}` |
| `intent_signals` | אותות השקעה | `{"signals": [...], "investment_readiness": "high", ...}` |
| `staked_balances` | יתרות staking | `[{"symbol": "stETH", "amount": 2.5, "usd": 8500}]` |
| `governance_balances` | יתרות governance | `[{"symbol": "UNI", "amount": 150, "usd": 0}]` |

---

#### **סנקציות ורסקון**
| עמודה | הסבר | ערכים |
|-------|------|-------|
| `sanctions_hit` | נמצא ברשימת סנקציות | `true` / `false` |
| `sanctions_list_name` | שם הרשימה | `ofac_sdn`, `eu_consolidated`, `israel_nbctf` |
| `sanctions_entity_name` | שם הישות המוסנקת | `Hamas`, `Garantex`, וכו' |
| `risk_flags_str` | דגלי סיכון | `SYBIL_RISK`, `SANCTIONS_HIT`, `INFRASTRUCTURE_WALLET` |

---

#### **מטא-דאטה**
| עמודה | הסבר | דוגמה |
|-------|------|-------|
| `confidence` | רמת ביטחון בזיהוי | 0.0-1.0 |
| `notes` | הערות | `Analysis completed in 2.34s.` |

---

## בדיקות סנקציות

המערכת בודקת כל ארנק מול **3 רשימות סנקציות בינלאומיות**:

### **1. OFAC SDN (ארה"ב)** 🇺🇸
- **שם מלא:** Office of Foreign Assets Control - Specially Designated Nationals
- **מקור:** משרד האוצר האמריקאי
- **כיסוי:** ~1000+ כתובות קריפטו
- **מטבעות:** BTC, ETH, USDT, XMR, LTC, TRX, BSC, ARB, SOL, ועוד 18 מטבעות

**דוגמאות:**
- ארגוני טרור (Hamas, Hezbollah)
- רוסיה (oligarchs, ransomware groups)
- צפון קוריאה (Lazarus Group)
- איראן (IRGC)

---

### **2. EU Consolidated (אירופה)** 🇪🇺
- **שם מלא:** EU Consolidated Sanctions List
- **מקור:** הנציבות האירופית
- **כיסוי:** ~50-100 כתובות קריפטו
- **מטבעות:** ETH, BTC, BSC, TRX

**דוגמאות:**
- בורסות קריפטו רוסיות (Garantex, Suex)
- ישויות תומכות מלחמה באוקראינה
- ארגוני טרור

---

### **3. Israel NBCTF (ישראל)** 🇮🇱
- **שם מלא:** National Bureau for Counter Terror Financing
- **מקור:** משרד הביטחון הישראלי
- **כיסוי:** משתנה (JSON)
- **מטבעות:** ETH, BTC, TRX

**דוגמאות:**
- ארגוני טרור (חמאס, חיזבאללה, PIJ)
- ארנקי גיוס כספים

---

### תהליך הבדיקה

1. **הורדה אוטומטית:** כל 24 שעות (ניתן להגדרה)
2. **ניתוח XML/JSON:** פיענוח כתובות קריפטו מהרשימות
3. **נרמול:** lowercase + trim
4. **אחסון:** טבלת `sanctions_addresses` עם אינדקס
5. **בדיקה:** השוואת כל ארנק מול הטבלה (O(1) בזכות אינדקס)

**זמן בדיקה:** ~1ms לארנק

---

### פלט סנקציות

אם נמצא התאמה:
```json
{
  "sanctions_hit": true,
  "sanctions_list_name": "ofac_sdn",
  "sanctions_entity_name": "GARANTEX OU",
  "risk_flags": ["SANCTIONS_HIT"]
}
```

**⚠️ חומרה:** סנקציות הן דגל אדום חמור - **אין לעבוד עם הארנק הזה.**

---

## דגלי סיכון

המערכת מזהה 6 סוגי דגלי סיכון:

### **1. SANCTIONS_HIT** 🚨 (חמור ביותר)
- **משמעות:** הארנק ברשימת סנקציות בינלאומית
- **המלצה:** **חסימה מיידית**, יש לדווח לרגולטור

---

### **2. SYBIL_RISK** ⚠️
- **תנאי:** sybil_risk_score ≥ 50
- **משמעות:** ארנק חשוד כ-Sybil/Farming
- **המלצה:** סנן לפני Airdrops, אל תספור בסטטיסטיקות משתמשים

---

### **3. LOW_VALUE_HIGH_ACTIVITY** 🔍
- **תנאי:** sybil_risk_score ≥ 30 AND < 50
- **משמעות:** דפוס פעילות חשוד (bot?)
- **המלצה:** בדיקה ידנית

---

### **4. INFRASTRUCTURE_WALLET** ⚙️
- **תנאי:** wallet_type ∈ {CEX, DEX_ROUTER, BRIDGE, PROTOCOL, CONTRACT}
- **משמעות:** לא משתמש אמיתי
- **המלצה:** אל תכלול במדדי "קהילה", אבל חשוב לצרכי נזילות

---

### **5. UNVERIFIED_OR_UNUSED_CONTRACT** 📜
- **תנאי:** is_contract = true AND tx_count = 0
- **משמעות:** חוזה שלא נעשה בו שימוש
- **המלצה:** בטל רישום אוטומטי, בדוק פונקציונליות

---

### **6. Community Health Flags** (ברמת הפרויקט)

#### **exchange_heavy** 🏦
- **תנאי:** >30% מהערך בארנקי CEX
- **חומרה:** צהוב (>30%), אדום (>50%)
- **פירוט:** "XX% of total value sits in CEX wallets"
- **המלצה:** "CEX wallets aggregate many users behind one address. Consider filtering them for accurate user metrics."

#### **sybil_cohort** 🚜
- **תנאי:** >20% מהארנקים עם sybil_risk_score ≥ 40
- **חומרה:** צהוב (>20%), אדום (>40%)
- **פירוט:** "XXX wallets (XX%) show sybil/farming patterns"
- **המלצה:** "Implement sybil filtering before airdrops or reward distributions to protect budgets."

#### **whale_concentration** 🐋
- **תנאי:** 5 הארנקים הגדולים מחזיקים >50% מהערך
- **חומרה:** צהוב (>50%), אדום (>80%)
- **פירוט:** "Top 5 wallets control XX% of total value"
- **המלצה:** "High concentration increases risk from individual wallet movements. Diversify holder base."

#### **low_user_ratio** 👥
- **תנאי:** <50% משתמשים אמיתיים
- **חומרה:** צהוב (<50%), אדום (<30%)
- **פירוט:** "Only XX% of wallets are real end-users"
- **המלצה:** "High infrastructure ratio may indicate bot activity or data quality issues. Review wallet classification."

#### **low_activity** 💤
- **תנאי:** ממוצע tx_count < 10
- **חומרה:** צהוב
- **פירוט:** "Average transaction count is X.X"
- **המלצה:** "Low activity suggests passive holders or dust wallets. Consider activation campaigns."

#### **sanctions_presence** 🚨
- **תנאי:** ≥1 ארנק מוסנק
- **חומרה:** אדום
- **פירוט:** "X wallet(s) matched international sanctions lists"
- **המלצה:** "Immediate compliance review required. Consider blocking sanctioned addresses."

#### **healthy** ✅
- **תנאי:** אין דגלים רעים
- **חומרה:** ירוק
- **פירוט:** "No significant risk flags detected"
- **המלצה:** "Community appears healthy. Continue monitoring with periodic re-analysis."

---

## מדדי ריכוז (Concentration Metrics)

### **1. Gini Coefficient** 📊
מדד אי-שוויון סטנדרטי (0-1).

**פרשנות:**
- **0.0-0.3:** שוויוני מאוד (Diversified)
- **0.3-0.6:** שוויוני בינוני (Moderate)
- **0.6-0.8:** מרוכז (Concentrated)
- **0.8-1.0:** מרוכז מאוד (Highly concentrated)

**דוגמה:**
- Gini = 0.25 → "Diversified"
- Gini = 0.75 → "Highly concentrated"

---

### **2. Top-N Shares**
אחוז השווי שמחזיקים N הארנקים הגדולים.

**מדדים:**
- **Top 1%**: כמה מחזיק העליון 1%?
- **Top 5%**: כמה מחזיק העליון 5%?
- **Top 10%**: כמה מחזיק העליון 10%?

**דוגמה:**
- Top 1% = 45% → ריכוז גבוה
- Top 10% = 65% → ריכוז בינוני

---

### **3. HHI (Herfindahl-Hirschman Index)**
מדד ריכוז רגולטורי (0-1).

**חישוב:**
```
HHI = Σ(market_share_i²)
```

**פרשנות (FTC/DOJ guidelines):**
- **<0.15:** לא מרוכז (Competitive)
- **0.15-0.25:** מרוכז מעט (Moderately concentrated)
- **>0.25:** מרוכז מאוד (Highly concentrated)

---

## הגדרות מתקדמות (Admin Settings)

דרך ממשק ה-Admin ניתן להגדיר:

### **Scoring Settings**
- סף Whale (ברירת מחדל: 55)
- סף Tuna (ברירת מחדל: 30)
- משקלות הציון (balance, activity, defi, reputation, sybil)

### **Sanctions Settings**
- Enable/Disable sanctions screening
- בחירת רשימות (OFAC / EU / Israel)
- Action on hit: flag / exclude / both
- תדירות עדכון אוטומטי (שעות)

### **Intelligence Settings**
- Token categories enabled
- Intent signals enabled
- Community score enabled
- Health flags enabled

### **Report Settings**
- איזה סקציות להציג בדוח
- Executive summary, community score, intelligence, risk, וכו'

### **Operational Settings**
- Max wallets per job (ברירת מחדל: 10,000)
- RPC timeout (שניות)
- Retry count

---

## סיכום

המערכת מספקת **אינטליגנציה רב-ממדית** על קהילות קריפטו:

✅ **ציון משקיע** (0-100) מ-5 מרכיבים
✅ **סיווג לרמות** (Whale/Tuna/Fish)
✅ **10 פרסונות** עם רמת ביטחון וראיות
✅ **ציון קהילה** (0-100, A+-F) מ-5 מרכיבים
✅ **אינטליגנציה על אחזקות** (5 קטגוריות טוקנים + ריכוז)
✅ **אותות כוונות השקעה** (6 אותות + readiness)
✅ **בדיקת סנקציות** (3 רשימות בינלאומיות)
✅ **דגלי בריאות** (6 דגלים אדום/צהוב/ירוק)
✅ **מדדי ריכוז** (Gini, Top-N%, HHI)

**פורמטים:**
- CSV (טבלה מלאה)
- JSON (נתונים גולמיים)
- HTML (דוח narrative)
- PDF (להדפסה)
- Word (לעריכה)

**תדירות מומלצת:** ניתוח מחדש כל 2-4 שבועות לקבלת snapshot עדכני.
