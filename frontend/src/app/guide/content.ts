export type Lang = "he" | "en";

interface ScoringComponent {
  name: string;
  weight: string;
  description: string;
  ranges: string[];
  formula?: string;
  color: string;
}

interface TierInfo {
  emoji: string;
  name: string;
  scoreRange: string;
  description: string;
  examples: string[];
  color: string;
}

interface WalletTypeRow {
  type: string;
  description: string;
  examples: string;
}

interface PersonaInfo {
  emoji: string;
  name: string;
  condition: string;
  confidence: string;
  color: string;
}

interface CommunityComponent {
  name: string;
  weight: string;
  description: string;
  color: string;
}

interface GradeRow {
  range: string;
  grade: string;
  color: string;
}

interface TokenCategory {
  icon: string;
  name: string;
  description: string;
  color: string;
}

interface IntentSignal {
  icon: string;
  name: string;
  description: string;
  color: string;
}

interface CsvGroup {
  title: string;
  items: [string, string][];
}

interface RiskFlag {
  icon: string;
  name: string;
  description: string;
  color: string;
}

interface CommunityFlag {
  flag: string;
  description: string;
}

interface GuideSection {
  headerTitle: string;
  headerSubtitle: string;
  tocTitle: string;
  tocItems: [string, string][];
  overviewTitle: string;
  overviewIntro: string;
  overviewProcessTitle: string;
  overviewSteps: string[];
  scoringTitle: string;
  scoringIntro: string;
  scoringComponents: ScoringComponent[];
  scoringTotalTitle: string;
  scoringTotalFormula: string;
  scoringTotalNote: string;
  tiersTitle: string;
  tiers: TierInfo[];
  tiersNote: string;
  walletTypesTitle: string;
  walletTypesIntro: string;
  walletTypeLayers: { title: string; description: string; color: string }[];
  walletTypeTableHeaders: [string, string, string];
  walletTypeRows: WalletTypeRow[];
  personasTitle: string;
  personasIntro: string;
  personas: PersonaInfo[];
  confidenceLabel: string;
  communityTitle: string;
  communityIntro: string;
  communityComponents: CommunityComponent[];
  gradesTitle: string;
  gradeTableHeaders: [string, string];
  grades: GradeRow[];
  holdingsTitle: string;
  holdingsIntro: string;
  tokenCategories: TokenCategory[];
  concentrationTitle: string;
  concentrationMetrics: string[];
  intentTitle: string;
  intentSignals: IntentSignal[];
  readinessTitle: string;
  readinessLevels: { level: string; description: string; color: string }[];
  csvTitle: string;
  csvInputsTitle: string;
  csvInputs: [string, string][];
  csvGroups: CsvGroup[];
  sanctionsTitle: string;
  sanctionsSources: { emoji: string; name: string; description: string; color: string }[];
  sanctionsNotes: { text: string; color: string }[];
  riskFlagsTitle: string;
  walletFlagsTitle: string;
  walletFlags: RiskFlag[];
  communityFlagsTitle: string;
  communityFlagHeaders: [string, string];
  communityFlags: CommunityFlag[];
}

export type GuideContent = Record<Lang, GuideSection>;

export const guideContent: GuideContent = {
  he: {
    headerTitle: "מדריך מערכת Wallet Intelligence",
    headerSubtitle: "הסבר מקיף על הניתוח, הציונים, הסיווגים והאינטליגנציה של המערכת",
    tocTitle: "תוכן עניינים",
    tocItems: [
      ["#overview", "1. מה המערכת בודקת?"],
      ["#scoring", "2. מערכת הציונים"],
      ["#tiers", "3. סיווג רמות"],
      ["#wallet-types", "4. סוגי ארנקים"],
      ["#personas", "5. פרסונות משתמשים"],
      ["#community", "6. ניקוד קהילה"],
      ["#holdings", "7. אינטליגנציה על אחזקות"],
      ["#intent", "8. אותות כוונות השקעה"],
      ["#csv", "9. הסבר עמודות CSV"],
      ["#sanctions", "10. בדיקות סנקציות"],
      ["#risk-flags", "11. דגלי סיכון"],
    ],

    // 1. Overview
    overviewTitle: "1. מה המערכת בודקת?",
    overviewIntro: "המערכת מנתחת ארנקי קריפטו ומספקת אינטליגנציה ברמת הקהילה וברמת הפרט.",
    overviewProcessTitle: "תהליך הניתוח:",
    overviewSteps: [
      "<strong>קריאת נתוני בלוקצ'יין:</strong> יתרות, מספר עסקאות, טוקנים",
      "<strong>זיהוי זהות:</strong> משתמש, בורסה, חוזה חכם, גשר?",
      "<strong>ציון רב-ממדי:</strong> 5 רכיבים עם משקלים (סה\"כ 0-100)",
      "<strong>סיווג רמה ופרסונה:</strong> Whale/Tuna/Fish/Infra + 10 פרסונות",
      "<strong>ניתוח החזקות:</strong> נייטיב, סטייבלקוין, staked, governance",
      "<strong>אותות כוונות השקעה:</strong> 6 סיגנלים",
      "<strong>ניקוד קהילה:</strong> 0-100 עם דירוג אותיות (A+ עד F)",
      "<strong>בדיקת סנקציות:</strong> OFAC, EU, Israel",
      "<strong>דגלי בריאות וסיכון:</strong> Sybil, תשתית, סנקציות",
    ],

    // 2. Scoring
    scoringTitle: "2. מערכת הציונים (Scoring System)",
    scoringIntro: "כל ארנק מקבל ציון משקיע (Investor Score) בין 0-100, המורכב מ-5 רכיבים:",
    scoringComponents: [
      {
        name: "1. Balance Score",
        weight: "משקל: 30%",
        description: "ציון לוגריתמי מבוסס על שווי נטו בדולרים:",
        ranges: [
          "$0-100 → 0-20 נקודות",
          "$100-1K → 20-40 נקודות",
          "$1K-10K → 40-60 נקודות",
          "$10K-100K → 60-80 נקודות",
          "$100K+ → 80-100 נקודות",
        ],
        formula: "min(100, 20 * log10(max(1, net_worth_usd)))",
        color: "green",
      },
      {
        name: "2. Activity Score",
        weight: "משקל: 15%",
        description: "ציון לוגריתמי מבוסס על מספר עסקאות:",
        ranges: [
          "0-10 tx → 0-20 נקודות",
          "10-50 tx → 20-40 נקודות",
          "50-200 tx → 40-60 נקודות",
          "200-1000 tx → 60-80 נקודות",
          "1000+ tx → 80-100 נקודות",
        ],
        formula: "min(100, 25 * log10(max(1, tx_count)))",
        color: "blue",
      },
      {
        name: "3. DeFi Investor Score",
        weight: "משקל: 25%",
        description: "מבוסס על מגוון טוקנים:",
        ranges: [
          "0-1 טוקנים → 0-20 נקודות",
          "2-3 טוקנים → 20-40 נקודות",
          "4-6 טוקנים → 40-60 נקודות",
          "7-10 טוקנים → 60-80 נקודות",
          "10+ טוקנים → 80-100 נקודות",
        ],
        formula: "min(100, 33 * log10(max(1, token_count)))",
        color: "purple",
      },
      {
        name: "4. Reputation Score",
        weight: "משקל: 20%",
        description: "מבוסס על תוויות מוכרות:",
        ranges: [
          "VC/KOL/Protocol → 90-100 נקודות",
          "High Activity → 75 נקודות",
          "DEX Router/Bridge → 70 נקודות",
          "CEX → 60 נקודות",
          "Unknown → 50 נקודות (ברירת מחדל)",
          "Inactive Holder → 40 נקודות",
          "Smart Contract → 30 נקודות",
        ],
        color: "yellow",
      },
      {
        name: "5. Sybil Risk Score",
        weight: "משקל: -10% (שלילי)",
        description: "יתרה נמוכה + פעילות גבוהה = חשד ל-Sybil:",
        ranges: [
          "net_worth < $100 AND tx > 50 → 60-80 נקודות",
          "net_worth < $10 → 90 נקודות",
          "אחרת → 0 נקודות",
        ],
        color: "red",
      },
    ],
    scoringTotalTitle: 'סה"כ Investor Score:',
    scoringTotalFormula: "(Balance x 0.30) + (Activity x 0.15) + (DeFi x 0.25) + (Reputation x 0.20) + (Sybil x -0.10)",
    scoringTotalNote: "* המשקלים ניתנים לשינוי דרך Admin Dashboard",

    // 3. Tiers
    tiersTitle: "3. סיווג רמות (Tiers)",
    tiers: [
      {
        emoji: "\u{1F40B}",
        name: "Whale",
        scoreRange: "ציון ≥ 55",
        description: "משקיעים גדולים עם נכסים משמעותיים ופעילות DeFi.",
        examples: ["שווי: $100K+", "עסקאות: 200+", "טוקנים: 7+"],
        color: "purple",
      },
      {
        emoji: "\u{1F41F}",
        name: "Tuna",
        scoreRange: "ציון 30-54",
        description: "משקיעים בינוניים עם פעילות סבירה.",
        examples: ["שווי: $5K-50K", "עסקאות: 50-200", "טוקנים: 3-6"],
        color: "blue",
      },
      {
        emoji: "\u{1F420}",
        name: "Fish",
        scoreRange: "ציון < 30",
        description: "משקיעים קטנים, מתחילים, או ארנקי dust.",
        examples: ["שווי: $100-1K", "עסקאות: 10-50", "טוקנים: 1-2"],
        color: "gray",
      },
      {
        emoji: "\u2699\uFE0F",
        name: "Infra",
        scoreRange: "תשתית",
        description: "CEX, DEX, BRIDGE, PROTOCOL או CONTRACT.",
        examples: ["אלו לא משתמשים אמיתיים אלא תשתית - לא מקבלים ציון משקיע."],
        color: "orange",
      },
    ],
    tiersNote: "שימו לב: ערכי הסף ניתנים לשינוי דרך Admin Dashboard.",

    // 4. Wallet Types
    walletTypesTitle: "4. סוגי ארנקים (Wallet Types)",
    walletTypesIntro: "7 סוגי ארנקים מזוהים דרך 3 שכבות:",
    walletTypeLayers: [
      { title: "שכבה A: JSON Labels", description: "בדיקה מול רשימת כתובות מוכרות: CEX_EXCHANGE, DEX_ROUTER, BRIDGE, PROTOCOL, VC, KOL", color: "green" },
      { title: "שכבה B: Contract Detection", description: "אם יש bytecode → CONTRACT", color: "blue" },
      { title: "שכבה C: Heuristic Fallback", description: "5000+ עסקאות + אין קוד → DEX_ROUTER חשוד, אחרת → USER", color: "purple" },
    ],
    walletTypeTableHeaders: ["סוג", "תיאור", "דוגמאות"],
    walletTypeRows: [
      { type: "USER", description: "משתמש רגיל", examples: "ארנקים אישיים, משקיעים" },
      { type: "CEX_EXCHANGE", description: "בורסה מרכזית", examples: "Binance, Coinbase, Kraken" },
      { type: "DEX_ROUTER", description: "נתב DEX", examples: "Uniswap Router, 1inch" },
      { type: "BRIDGE", description: "גשר בין רשתות", examples: "Stargate, Wormhole" },
      { type: "PROTOCOL", description: "פרוטוקול DeFi", examples: "Aave, Compound, Lido" },
      { type: "CONTRACT", description: "חוזה חכם כללי", examples: "טוקנים, NFTs" },
      { type: "UNKNOWN", description: "לא ידוע", examples: "לא זוהה" },
    ],

    // 5. Personas
    personasTitle: "5. פרסונות משתמשים (Personas)",
    personasIntro: "המערכת מזהה 10 פרסונות שונות:",
    personas: [
      { emoji: "\u{1F40B}", name: "Whale Investor", condition: "ציון ≥ 70 וגם שווי ≥ $100K", confidence: "0.95", color: "purple" },
      { emoji: "\u{1F9BE}", name: "DeFi Native", condition: "ציון DeFi ≥ 60 וגם 5+ טוקנים", confidence: "0.85", color: "indigo" },
      { emoji: "\u{1F512}", name: "Staker", condition: "מעל 30% מהאחזקות ב-staked", confidence: "0.80", color: "blue" },
      { emoji: "\u{1F5F3}\uFE0F", name: "Governance Participant", condition: "מחזיק טוקני גוברננס (UNI/AAVE/LDO/MKR)", confidence: "0.75", color: "green" },
      { emoji: "\u{1F4CA}", name: "Active Trader", condition: "200+ עסקאות וגם Activity ≥ 60", confidence: "0.70", color: "yellow" },
      { emoji: "\u{1F4B5}", name: "Stablecoin Holder", condition: "מעל 60% מהשווי בסטייבלקוין", confidence: "0.65", color: "teal" },
      { emoji: "\u{1F195}", name: "Newcomer", condition: "עד 5 עסקאות ושווי מתחת ל-$1K", confidence: "0.60", color: "cyan" },
      { emoji: "\u{1F69C}", name: "Sybil/Farmer", condition: "סיכון Sybil ≥ 60", confidence: "0.80", color: "red" },
      { emoji: "\u{1F4A4}", name: "Passive Investor", condition: "פחות מ-20 עסקאות ושווי ≥ $5K", confidence: "0.55", color: "orange" },
      { emoji: "\u{1F464}", name: "Casual User", condition: "ברירת מחדל", confidence: "0.50", color: "gray" },
    ],
    confidenceLabel: "אמינות",

    // 6. Community Score
    communityTitle: "6. ניקוד קהילה (Community Score)",
    communityIntro: "ציון ברמת הפרוייקט (0-100) עם דירוג אותיות (A+ עד F), מורכב מ-5 רכיבים:",
    communityComponents: [
      { name: "User Ratio", weight: "משקל: 30%", description: 'אחוז משתמשים אמיתיים (לא תשתית). 70%+ → 100 נקודות', color: "blue" },
      { name: "Investor Quality", weight: "משקל: 25%", description: "ממוצע ציון המשקיעים של הפרוייקט", color: "purple" },
      { name: "Diversity", weight: "משקל: 15%", description: "אנטרופיית Shannon של הפרסונות (גיוון גבוה = טוב)", color: "green" },
      { name: "Whale Presence", weight: "משקל: 15%", description: "נקודה מתוקה: 5-15% Whales", color: "yellow" },
      { name: "Health Signals", weight: "משקל: 15%", description: "היפוך של יחס Sybil + סנקציות", color: "red" },
    ],
    gradesTitle: "דירוגי אותיות:",
    gradeTableHeaders: ["טווח ציון", "דירוג"],
    grades: [
      { range: "90-100", grade: "A+", color: "green" },
      { range: "85-89", grade: "A", color: "green" },
      { range: "80-84", grade: "A-", color: "green" },
      { range: "75-79", grade: "B+", color: "blue" },
      { range: "70-74", grade: "B", color: "blue" },
      { range: "65-69", grade: "B-", color: "blue" },
      { range: "60-64", grade: "C+", color: "yellow" },
      { range: "55-59", grade: "C", color: "yellow" },
      { range: "50-54", grade: "C-", color: "yellow" },
      { range: "40-49", grade: "D", color: "orange" },
      { range: "0-39", grade: "F", color: "red" },
    ],

    // 7. Token Intelligence
    holdingsTitle: "7. אינטליגנציה על אחזקות (Token Intelligence)",
    holdingsIntro: "המערכת מסווגת טוקנים ל-4 קטגוריות:",
    tokenCategories: [
      { icon: "\u{1F537}", name: "Native", description: "הטוקן של הרשת: ETH, SOL, MATIC", color: "blue" },
      { icon: "\u{1F4B5}", name: "Stablecoin", description: "מטבעות יציבים: USDC, USDT, DAI", color: "green" },
      { icon: "\u{1F512}", name: "Staked", description: "נכסים ב-staking: stETH, rETH, cbETH", color: "purple" },
      { icon: "\u{1F5F3}\uFE0F", name: "Governance", description: "טוקני גוברננס: UNI, AAVE, LDO, MKR", color: "orange" },
    ],
    concentrationTitle: "מטריקות ריכוז:",
    concentrationMetrics: [
      "<strong>HHI:</strong> מדד ריכוז (0-1). 0 = מפוזר, 1 = מרוכז בנכס יחיד",
      '<strong>Stablecoin Share:</strong> אחוז השווי בסטייבלקוין. &gt;60% = "Dry Powder"',
      "<strong>Staked Share:</strong> אחוז השווי ב-staking. &gt;30% = Staker",
      "<strong>Gini Coefficient:</strong> מדד אי-שוויון (0-1). &gt;0.6 = מרוכז",
    ],

    // 8. Investment Intent
    intentTitle: "8. אותות כוונות השקעה (Investment Intent)",
    intentSignals: [
      { icon: "\u{1F4A7}", name: "Dry Powder", description: "מעל 50% סטייבלקוין → מוכן להשקיע", color: "green" },
      { icon: "\u{1F512}", name: "Long-Term Commitment", description: "מעל 20% staked → מחויבות לטווח ארוך", color: "blue" },
      { icon: "\u{1F5F3}\uFE0F", name: "Governance Participant", description: "מחזיק טוקני גוברננס → מעורב בפרוטוקולים", color: "purple" },
      { icon: "\u{1F4CA}", name: "Diversified Portfolio", description: "5+ טוקנים שונים → גיוון השקעות", color: "yellow" },
      { icon: "\u{1F3AF}", name: "Concentrated Position", description: "מעל 70% בנכס יחיד → משקיע ממוקד", color: "orange" },
      { icon: "\u{1F525}", name: "Active Trader", description: "200+ עסקאות → סוחר פעיל", color: "red" },
    ],
    readinessTitle: "Investment Readiness:",
    readinessLevels: [
      { level: "High", description: "3+ סיגנלים חזקים", color: "green" },
      { level: "Medium", description: "1-2 סיגנלים", color: "yellow" },
      { level: "Low", description: "אין סיגנלים משמעותיים", color: "gray" },
    ],

    // 9. CSV Columns
    csvTitle: "9. הסבר על עמודות ה-CSV/Excel",
    csvInputsTitle: "קלטים (Inputs):",
    csvInputs: [
      ["address", "כתובת הארנק"],
      ["chain", "שם הרשת (ethereum, polygon, base, arbitrum, solana)"],
    ],
    csvGroups: [
      {
        title: "סיווגים בסיסיים",
        items: [
          ["tier", "Whale / Tuna / Fish / Infra"],
          ["wallet_type", "USER / CEX_EXCHANGE / DEX_ROUTER / BRIDGE / PROTOCOL / CONTRACT / UNKNOWN"],
          ["persona", "שם הפרסונה (10 אפשרויות)"],
        ],
      },
      {
        title: "מידע כלכלי",
        items: [
          ["native_balance", "יתרת הטוקן המקורי (ETH/SOL)"],
          ["est_net_worth_usd", "שווי נטו משוער בדולרים"],
          ["stable_usd_total", "סך סטייבלקוין בדולרים"],
        ],
      },
      {
        title: "ציונים (0-100)",
        items: [
          ["investor_score", "ציון משקיע כולל"],
          ["balance_score", "רכיב יתרה"],
          ["activity_score", "רכיב פעילות"],
          ["defi_investor_score", "רכיב DeFi"],
          ["reputation_score", "רכיב מוניטין"],
          ["sybil_risk_score", "רכיב סיכון Sybil"],
          ["product_relevance_score", "רלוונטיות למוצר"],
        ],
      },
      {
        title: "פעילות וזיהוי",
        items: [
          ["tx_count", "מספר עסקאות"],
          ["is_contract", "האם חוזה חכם (true/false)"],
          ["known_entity_type", "סוג ישות מוכר (VC/KOL/CEX)"],
          ["labels_str", "תוויות ידועות"],
        ],
      },
      {
        title: "אינטליגנציה מתקדמת (JSON)",
        items: [
          ["token_intelligence", "פילוח קטגוריות טוקנים + HHI + shares"],
          ["persona_detail", "שם פרסונה, אמינות, נימוקים"],
          ["intent_signals", "רשימת סיגנלים + investment_readiness"],
          ["staked_balances", "פירוט נכסי staking"],
          ["governance_balances", "פירוט טוקני גוברננס"],
        ],
      },
      {
        title: "סנקציות וסיכונים",
        items: [
          ["sanctions_hit", "האם זוהתה סנקציה (true/false)"],
          ["sanctions_list_name", "שם הרשימה (OFAC/EU/Israel)"],
          ["sanctions_entity_name", "שם הישות המוסנקצת"],
          ["risk_flags_str", "דגלי סיכון (מופרדים בפסיק)"],
        ],
      },
    ],

    // 10. Sanctions
    sanctionsTitle: "10. בדיקות סנקציות",
    sanctionsSources: [
      { emoji: "\u{1F1FA}\u{1F1F8}", name: "OFAC SDN", description: "משרד האוצר האמריקאי", color: "blue" },
      { emoji: "\u{1F1EA}\u{1F1FA}", name: "EU Consolidated", description: "האיחוד האירופי", color: "yellow" },
      { emoji: "\u{1F1EE}\u{1F1F1}", name: "Israel NBCTF", description: "הרשות להלבנת הון", color: "purple" },
    ],
    sanctionsNotes: [
      { text: "<strong>עדכון אוטומטי:</strong> כל 24 שעות דרך Celery Beat", color: "green" },
      { text: "<strong>מהירות בדיקה:</strong> ~1ms לארנק (אינדקס מקומי)", color: "blue" },
      { text: "<strong>בהתאמה:</strong> sanctions_hit=true, דגל SANCTIONS_HIT, שם ישות ורשימה", color: "red" },
    ],

    // 11. Risk Flags
    riskFlagsTitle: "11. דגלי סיכון (Risk Flags)",
    walletFlagsTitle: "דגלים ברמת ארנק:",
    walletFlags: [
      { icon: "\u{1F6A8}", name: "SANCTIONS_HIT", description: "הארנק מופיע ברשימת סנקציות (החמור ביותר)", color: "red" },
      { icon: "\u26A0\uFE0F", name: "SYBIL_RISK", description: "חשד ל-Sybil attack או farming (ציון ≥ 60)", color: "orange" },
      { icon: "\u26A1", name: "LOW_VALUE_HIGH_ACTIVITY", description: "שווי נמוך + פעילות גבוהה", color: "yellow" },
      { icon: "\u{1F3ED}", name: "INFRASTRUCTURE_WALLET", description: "ארנק תשתית (CEX/DEX/Bridge/Protocol)", color: "blue" },
      { icon: "\u{1F4DC}", name: "UNVERIFIED_CONTRACT", description: "חוזה חכם שלא אומת או לא בשימוש", color: "purple" },
    ],
    communityFlagsTitle: "דגלים ברמת הקהילה:",
    communityFlagHeaders: ["דגל", "תיאור"],
    communityFlags: [
      { flag: "exchange_heavy", description: "יותר מ-30% מהערך בארנקי בורסות" },
      { flag: "sybil_cohort", description: "יותר מ-20% עם דפוס Sybil" },
      { flag: "whale_concentration", description: "Top 5 מחזיקים מעל 50% מהערך" },
      { flag: "low_user_ratio", description: "פחות מ-50% משתמשים אמיתיים" },
      { flag: "low_activity", description: "ממוצע פעילות נמוך (< 10 tx)" },
      { flag: "sanctions_presence", description: "קיימים ארנקים מוסנקצים" },
      { flag: "healthy \u2705", description: "אין דגלי סיכון משמעותיים" },
    ],
  },

  en: {
    headerTitle: "Wallet Intelligence System Guide",
    headerSubtitle: "Comprehensive guide to analysis, scores, classifications, and intelligence",
    tocTitle: "Table of Contents",
    tocItems: [
      ["#overview", "1. What Does the System Analyze?"],
      ["#scoring", "2. Scoring System"],
      ["#tiers", "3. Tier Classification"],
      ["#wallet-types", "4. Wallet Types"],
      ["#personas", "5. User Personas"],
      ["#community", "6. Community Score"],
      ["#holdings", "7. Token Intelligence (Holdings)"],
      ["#intent", "8. Investment Intent Signals"],
      ["#csv", "9. CSV/Excel Column Reference"],
      ["#sanctions", "10. Sanctions Screening"],
      ["#risk-flags", "11. Risk Flags"],
    ],

    // 1. Overview
    overviewTitle: "1. What Does the System Analyze?",
    overviewIntro: "The system analyzes crypto wallets and provides intelligence at both the community and individual levels.",
    overviewProcessTitle: "Analysis Process:",
    overviewSteps: [
      "<strong>Blockchain Data Reading:</strong> balances, transaction count, tokens",
      "<strong>Identity Detection:</strong> user, exchange, smart contract, bridge?",
      "<strong>Multi-Dimensional Scoring:</strong> 5 components with weights (total 0-100)",
      "<strong>Tier & Persona Classification:</strong> Whale/Tuna/Fish/Infra + 10 personas",
      "<strong>Holdings Analysis:</strong> native, stablecoin, staked, governance",
      "<strong>Investment Intent Signals:</strong> 6 signals",
      "<strong>Community Scoring:</strong> 0-100 with letter grades (A+ to F)",
      "<strong>Sanctions Screening:</strong> OFAC, EU, Israel",
      "<strong>Health & Risk Flags:</strong> Sybil, infrastructure, sanctions",
    ],

    // 2. Scoring
    scoringTitle: "2. Scoring System",
    scoringIntro: "Each wallet receives an Investor Score between 0-100, composed of 5 components:",
    scoringComponents: [
      {
        name: "1. Balance Score",
        weight: "Weight: 30%",
        description: "Logarithmic score based on net worth in USD:",
        ranges: [
          "$0-100 \u2192 0-20 points",
          "$100-1K \u2192 20-40 points",
          "$1K-10K \u2192 40-60 points",
          "$10K-100K \u2192 60-80 points",
          "$100K+ \u2192 80-100 points",
        ],
        formula: "min(100, 20 * log10(max(1, net_worth_usd)))",
        color: "green",
      },
      {
        name: "2. Activity Score",
        weight: "Weight: 15%",
        description: "Logarithmic score based on transaction count:",
        ranges: [
          "0-10 tx \u2192 0-20 points",
          "10-50 tx \u2192 20-40 points",
          "50-200 tx \u2192 40-60 points",
          "200-1000 tx \u2192 60-80 points",
          "1000+ tx \u2192 80-100 points",
        ],
        formula: "min(100, 25 * log10(max(1, tx_count)))",
        color: "blue",
      },
      {
        name: "3. DeFi Investor Score",
        weight: "Weight: 25%",
        description: "Based on token diversity:",
        ranges: [
          "0-1 tokens \u2192 0-20 points",
          "2-3 tokens \u2192 20-40 points",
          "4-6 tokens \u2192 40-60 points",
          "7-10 tokens \u2192 60-80 points",
          "10+ tokens \u2192 80-100 points",
        ],
        formula: "min(100, 33 * log10(max(1, token_count)))",
        color: "purple",
      },
      {
        name: "4. Reputation Score",
        weight: "Weight: 20%",
        description: "Based on known labels:",
        ranges: [
          "VC/KOL/Protocol \u2192 90-100 points",
          "High Activity \u2192 75 points",
          "DEX Router/Bridge \u2192 70 points",
          "CEX \u2192 60 points",
          "Unknown \u2192 50 points (default)",
          "Inactive Holder \u2192 40 points",
          "Smart Contract \u2192 30 points",
        ],
        color: "yellow",
      },
      {
        name: "5. Sybil Risk Score",
        weight: "Weight: -10% (negative)",
        description: "Low balance + high activity = Sybil suspicion:",
        ranges: [
          "net_worth < $100 AND tx > 50 \u2192 60-80 points",
          "net_worth < $10 \u2192 90 points",
          "Otherwise \u2192 0 points",
        ],
        color: "red",
      },
    ],
    scoringTotalTitle: "Total Investor Score:",
    scoringTotalFormula: "(Balance x 0.30) + (Activity x 0.15) + (DeFi x 0.25) + (Reputation x 0.20) + (Sybil x -0.10)",
    scoringTotalNote: "* Weights are configurable via the Admin Dashboard",

    // 3. Tiers
    tiersTitle: "3. Tier Classification",
    tiers: [
      {
        emoji: "\u{1F40B}",
        name: "Whale",
        scoreRange: "Score \u2265 55",
        description: "Large investors with significant assets and DeFi activity.",
        examples: ["Net worth: $100K+", "Transactions: 200+", "Tokens: 7+"],
        color: "purple",
      },
      {
        emoji: "\u{1F41F}",
        name: "Tuna",
        scoreRange: "Score 30-54",
        description: "Mid-tier investors with reasonable activity.",
        examples: ["Net worth: $5K-50K", "Transactions: 50-200", "Tokens: 3-6"],
        color: "blue",
      },
      {
        emoji: "\u{1F420}",
        name: "Fish",
        scoreRange: "Score < 30",
        description: "Small investors, newcomers, or dust wallets.",
        examples: ["Net worth: $100-1K", "Transactions: 10-50", "Tokens: 1-2"],
        color: "gray",
      },
      {
        emoji: "\u2699\uFE0F",
        name: "Infra",
        scoreRange: "Infrastructure",
        description: "CEX, DEX, BRIDGE, PROTOCOL or CONTRACT.",
        examples: ["These are not real users but infrastructure \u2014 they do not receive investor scores."],
        color: "orange",
      },
    ],
    tiersNote: "Note: Threshold values are configurable via the Admin Dashboard.",

    // 4. Wallet Types
    walletTypesTitle: "4. Wallet Types",
    walletTypesIntro: "7 wallet types identified through 3 detection layers:",
    walletTypeLayers: [
      { title: "Layer A: JSON Labels", description: "Check against known address list: CEX_EXCHANGE, DEX_ROUTER, BRIDGE, PROTOCOL, VC, KOL", color: "green" },
      { title: "Layer B: Contract Detection", description: "If bytecode exists \u2192 CONTRACT", color: "blue" },
      { title: "Layer C: Heuristic Fallback", description: "5000+ transactions + no code \u2192 suspected DEX_ROUTER, otherwise \u2192 USER", color: "purple" },
    ],
    walletTypeTableHeaders: ["Type", "Description", "Examples"],
    walletTypeRows: [
      { type: "USER", description: "Regular user", examples: "Personal wallets, investors" },
      { type: "CEX_EXCHANGE", description: "Centralized exchange", examples: "Binance, Coinbase, Kraken" },
      { type: "DEX_ROUTER", description: "DEX router", examples: "Uniswap Router, 1inch" },
      { type: "BRIDGE", description: "Cross-chain bridge", examples: "Stargate, Wormhole" },
      { type: "PROTOCOL", description: "DeFi protocol", examples: "Aave, Compound, Lido" },
      { type: "CONTRACT", description: "Generic smart contract", examples: "Tokens, NFTs" },
      { type: "UNKNOWN", description: "Unknown", examples: "Not identified" },
    ],

    // 5. Personas
    personasTitle: "5. User Personas",
    personasIntro: "The system identifies 10 distinct personas:",
    personas: [
      { emoji: "\u{1F40B}", name: "Whale Investor", condition: "Score \u2265 70 AND net worth \u2265 $100K", confidence: "0.95", color: "purple" },
      { emoji: "\u{1F9BE}", name: "DeFi Native", condition: "DeFi score \u2265 60 AND 5+ tokens", confidence: "0.85", color: "indigo" },
      { emoji: "\u{1F512}", name: "Staker", condition: "Over 30% of holdings in staked assets", confidence: "0.80", color: "blue" },
      { emoji: "\u{1F5F3}\uFE0F", name: "Governance Participant", condition: "Holds governance tokens (UNI/AAVE/LDO/MKR)", confidence: "0.75", color: "green" },
      { emoji: "\u{1F4CA}", name: "Active Trader", condition: "200+ transactions AND Activity \u2265 60", confidence: "0.70", color: "yellow" },
      { emoji: "\u{1F4B5}", name: "Stablecoin Holder", condition: "Over 60% of net worth in stablecoins", confidence: "0.65", color: "teal" },
      { emoji: "\u{1F195}", name: "Newcomer", condition: "Up to 5 transactions and net worth under $1K", confidence: "0.60", color: "cyan" },
      { emoji: "\u{1F69C}", name: "Sybil/Farmer", condition: "Sybil risk \u2265 60", confidence: "0.80", color: "red" },
      { emoji: "\u{1F4A4}", name: "Passive Investor", condition: "Less than 20 transactions and net worth \u2265 $5K", confidence: "0.55", color: "orange" },
      { emoji: "\u{1F464}", name: "Casual User", condition: "Default", confidence: "0.50", color: "gray" },
    ],
    confidenceLabel: "Confidence",

    // 6. Community Score
    communityTitle: "6. Community Score",
    communityIntro: "Project-level score (0-100) with letter grades (A+ to F), composed of 5 components:",
    communityComponents: [
      { name: "User Ratio", weight: "Weight: 30%", description: "Percentage of real users (not infrastructure). 70%+ \u2192 100 points", color: "blue" },
      { name: "Investor Quality", weight: "Weight: 25%", description: "Average investor score of the project", color: "purple" },
      { name: "Diversity", weight: "Weight: 15%", description: "Shannon entropy of personas (high diversity = good)", color: "green" },
      { name: "Whale Presence", weight: "Weight: 15%", description: "Sweet spot: 5-15% Whales", color: "yellow" },
      { name: "Health Signals", weight: "Weight: 15%", description: "Inverse of Sybil ratio + sanctions", color: "red" },
    ],
    gradesTitle: "Letter Grades:",
    gradeTableHeaders: ["Score Range", "Grade"],
    grades: [
      { range: "90-100", grade: "A+", color: "green" },
      { range: "85-89", grade: "A", color: "green" },
      { range: "80-84", grade: "A-", color: "green" },
      { range: "75-79", grade: "B+", color: "blue" },
      { range: "70-74", grade: "B", color: "blue" },
      { range: "65-69", grade: "B-", color: "blue" },
      { range: "60-64", grade: "C+", color: "yellow" },
      { range: "55-59", grade: "C", color: "yellow" },
      { range: "50-54", grade: "C-", color: "yellow" },
      { range: "40-49", grade: "D", color: "orange" },
      { range: "0-39", grade: "F", color: "red" },
    ],

    // 7. Token Intelligence
    holdingsTitle: "7. Token Intelligence (Holdings)",
    holdingsIntro: "The system classifies tokens into 4 categories:",
    tokenCategories: [
      { icon: "\u{1F537}", name: "Native", description: "Network's native token: ETH, SOL, MATIC", color: "blue" },
      { icon: "\u{1F4B5}", name: "Stablecoin", description: "Stable currencies: USDC, USDT, DAI", color: "green" },
      { icon: "\u{1F512}", name: "Staked", description: "Staked assets: stETH, rETH, cbETH", color: "purple" },
      { icon: "\u{1F5F3}\uFE0F", name: "Governance", description: "Governance tokens: UNI, AAVE, LDO, MKR", color: "orange" },
    ],
    concentrationTitle: "Concentration Metrics:",
    concentrationMetrics: [
      "<strong>HHI:</strong> Concentration index (0-1). 0 = diversified, 1 = concentrated in single asset",
      '<strong>Stablecoin Share:</strong> Percentage of value in stablecoins. &gt;60% = "Dry Powder"',
      "<strong>Staked Share:</strong> Percentage of value in staking. &gt;30% = Staker",
      "<strong>Gini Coefficient:</strong> Inequality measure (0-1). &gt;0.6 = concentrated",
    ],

    // 8. Investment Intent
    intentTitle: "8. Investment Intent Signals",
    intentSignals: [
      { icon: "\u{1F4A7}", name: "Dry Powder", description: "Over 50% stablecoins \u2192 ready to invest", color: "green" },
      { icon: "\u{1F512}", name: "Long-Term Commitment", description: "Over 20% staked \u2192 long-term commitment", color: "blue" },
      { icon: "\u{1F5F3}\uFE0F", name: "Governance Participant", description: "Holds governance tokens \u2192 engaged in protocols", color: "purple" },
      { icon: "\u{1F4CA}", name: "Diversified Portfolio", description: "5+ different tokens \u2192 investment diversification", color: "yellow" },
      { icon: "\u{1F3AF}", name: "Concentrated Position", description: "Over 70% in a single asset \u2192 focused investor", color: "orange" },
      { icon: "\u{1F525}", name: "Active Trader", description: "200+ transactions \u2192 active trader", color: "red" },
    ],
    readinessTitle: "Investment Readiness:",
    readinessLevels: [
      { level: "High", description: "3+ strong signals", color: "green" },
      { level: "Medium", description: "1-2 signals", color: "yellow" },
      { level: "Low", description: "No significant signals", color: "gray" },
    ],

    // 9. CSV Columns
    csvTitle: "9. CSV/Excel Column Reference",
    csvInputsTitle: "Inputs:",
    csvInputs: [
      ["address", "Wallet address"],
      ["chain", "Network name (ethereum, polygon, base, arbitrum, solana)"],
    ],
    csvGroups: [
      {
        title: "Basic Classifications",
        items: [
          ["tier", "Whale / Tuna / Fish / Infra"],
          ["wallet_type", "USER / CEX_EXCHANGE / DEX_ROUTER / BRIDGE / PROTOCOL / CONTRACT / UNKNOWN"],
          ["persona", "Persona name (10 options)"],
        ],
      },
      {
        title: "Financial Information",
        items: [
          ["native_balance", "Native token balance (ETH/SOL)"],
          ["est_net_worth_usd", "Estimated net worth in USD"],
          ["stable_usd_total", "Total stablecoin value in USD"],
        ],
      },
      {
        title: "Scores (0-100)",
        items: [
          ["investor_score", "Overall investor score"],
          ["balance_score", "Balance component"],
          ["activity_score", "Activity component"],
          ["defi_investor_score", "DeFi component"],
          ["reputation_score", "Reputation component"],
          ["sybil_risk_score", "Sybil risk component"],
          ["product_relevance_score", "Product relevance"],
        ],
      },
      {
        title: "Activity & Identification",
        items: [
          ["tx_count", "Transaction count"],
          ["is_contract", "Is smart contract (true/false)"],
          ["known_entity_type", "Known entity type (VC/KOL/CEX)"],
          ["labels_str", "Known labels"],
        ],
      },
      {
        title: "Advanced Intelligence (JSON)",
        items: [
          ["token_intelligence", "Token category breakdown + HHI + shares"],
          ["persona_detail", "Persona name, confidence, reasoning"],
          ["intent_signals", "Signal list + investment_readiness"],
          ["staked_balances", "Staking asset details"],
          ["governance_balances", "Governance token details"],
        ],
      },
      {
        title: "Sanctions & Risks",
        items: [
          ["sanctions_hit", "Sanction detected (true/false)"],
          ["sanctions_list_name", "List name (OFAC/EU/Israel)"],
          ["sanctions_entity_name", "Sanctioned entity name"],
          ["risk_flags_str", "Risk flags (comma-separated)"],
        ],
      },
    ],

    // 10. Sanctions
    sanctionsTitle: "10. Sanctions Screening",
    sanctionsSources: [
      { emoji: "\u{1F1FA}\u{1F1F8}", name: "OFAC SDN", description: "US Treasury Department", color: "blue" },
      { emoji: "\u{1F1EA}\u{1F1FA}", name: "EU Consolidated", description: "European Union", color: "yellow" },
      { emoji: "\u{1F1EE}\u{1F1F1}", name: "Israel NBCTF", description: "Anti-Money Laundering Authority", color: "purple" },
    ],
    sanctionsNotes: [
      { text: "<strong>Automatic Update:</strong> Every 24 hours via Celery Beat", color: "green" },
      { text: "<strong>Check Speed:</strong> ~1ms per wallet (local index)", color: "blue" },
      { text: "<strong>On Match:</strong> sanctions_hit=true, SANCTIONS_HIT flag, entity and list name", color: "red" },
    ],

    // 11. Risk Flags
    riskFlagsTitle: "11. Risk Flags",
    walletFlagsTitle: "Wallet-Level Flags:",
    walletFlags: [
      { icon: "\u{1F6A8}", name: "SANCTIONS_HIT", description: "Wallet appears on a sanctions list (most severe)", color: "red" },
      { icon: "\u26A0\uFE0F", name: "SYBIL_RISK", description: "Suspected Sybil attack or farming (score \u2265 60)", color: "orange" },
      { icon: "\u26A1", name: "LOW_VALUE_HIGH_ACTIVITY", description: "Low net worth + high activity", color: "yellow" },
      { icon: "\u{1F3ED}", name: "INFRASTRUCTURE_WALLET", description: "Infrastructure wallet (CEX/DEX/Bridge/Protocol)", color: "blue" },
      { icon: "\u{1F4DC}", name: "UNVERIFIED_CONTRACT", description: "Unverified or unused smart contract", color: "purple" },
    ],
    communityFlagsTitle: "Community-Level Flags:",
    communityFlagHeaders: ["Flag", "Description"],
    communityFlags: [
      { flag: "exchange_heavy", description: "Over 30% of value in exchange wallets" },
      { flag: "sybil_cohort", description: "Over 20% with Sybil pattern" },
      { flag: "whale_concentration", description: "Top 5 holders over 50% of value" },
      { flag: "low_user_ratio", description: "Less than 50% real users" },
      { flag: "low_activity", description: "Low average activity (< 10 tx)" },
      { flag: "sanctions_presence", description: "Sanctioned wallets present" },
      { flag: "healthy \u2705", description: "No significant risk flags" },
    ],
  },
};
