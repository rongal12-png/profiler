"use client";

import { useState } from "react";
import { guideContent, Lang } from "./content";

export default function GuidePage() {
  const [lang, setLang] = useState<Lang>("he");
  const c = guideContent[lang];
  const isRtl = lang === "he";

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-50 to-gray-100" dir={isRtl ? "rtl" : "ltr"}>
      {/* Header */}
      <div className="bg-gradient-to-r from-blue-600 to-purple-600 text-white py-12 px-6 shadow-lg">
        <div className="max-w-7xl mx-auto">
          <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 mb-4">
            <h1 className="text-4xl md:text-5xl font-bold">{c.headerTitle}</h1>
            <div className="flex items-center gap-3">
              {/* Language Toggle */}
              <button
                onClick={() => setLang(lang === "he" ? "en" : "he")}
                className="bg-white/20 hover:bg-white/30 text-white px-4 py-2 rounded-full text-sm font-semibold transition backdrop-blur-sm border border-white/30"
              >
                {lang === "he" ? "English" : "\u05E2\u05D1\u05E8\u05D9\u05EA"}
              </button>
              {/* PDF Download */}
              <a
                href={`/api/guide/pdf?lang=${lang}`}
                className="bg-white/20 hover:bg-white/30 text-white px-4 py-2 rounded-full text-sm font-semibold transition backdrop-blur-sm border border-white/30 flex items-center gap-2"
                download
              >
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                </svg>
                PDF
              </a>
            </div>
          </div>
          <p className="text-xl text-blue-100">{c.headerSubtitle}</p>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-4 py-8 lg:flex lg:gap-8">
        {/* Sidebar TOC */}
        <aside className="hidden lg:block lg:w-64 flex-shrink-0">
          <div className="sticky top-8 bg-white rounded-lg shadow-md p-6 border border-gray-200">
            <h2 className="text-lg font-bold mb-4 text-gray-800 border-b pb-2">{c.tocTitle}</h2>
            <nav className="space-y-2">
              {c.tocItems.map(([href, label]) => (
                <a key={href} href={href} className="block text-sm text-blue-600 hover:text-blue-800 hover:underline">
                  {label}
                </a>
              ))}
            </nav>
          </div>
        </aside>

        {/* Content */}
        <main className="flex-1 space-y-8">
          {/* Mobile TOC */}
          <div className="lg:hidden bg-white rounded-lg shadow-md p-6 border border-gray-200">
            <h2 className="text-lg font-bold mb-4 text-gray-800">{c.tocTitle}</h2>
            <nav className="grid grid-cols-1 sm:grid-cols-2 gap-2">
              {c.tocItems.map(([href, label]) => (
                <a key={href} href={href} className="text-sm text-blue-600 hover:underline">
                  {label}
                </a>
              ))}
            </nav>
          </div>

          {/* 1. Overview */}
          <section id="overview" className="bg-white rounded-lg shadow-md p-8 border border-gray-200 scroll-mt-8">
            <h2 className="text-3xl font-bold mb-6 text-gray-800 border-b-2 border-blue-500 pb-3">
              {c.overviewTitle}
            </h2>
            <p className="text-gray-700 mb-4 leading-relaxed">{c.overviewIntro}</p>
            <div className={`bg-blue-50 ${isRtl ? "border-r-4" : "border-l-4"} border-blue-500 p-6 rounded`}>
              <h3 className="font-bold text-lg mb-3 text-blue-900">{c.overviewProcessTitle}</h3>
              <ol className="list-decimal list-inside space-y-2 text-gray-700">
                {c.overviewSteps.map((step, i) => (
                  <li key={i} dangerouslySetInnerHTML={{ __html: step }} />
                ))}
              </ol>
            </div>
          </section>

          {/* 2. Scoring */}
          <section id="scoring" className="bg-white rounded-lg shadow-md p-8 border border-gray-200 scroll-mt-8">
            <h2 className="text-3xl font-bold mb-6 text-gray-800 border-b-2 border-purple-500 pb-3">
              {c.scoringTitle}
            </h2>
            <p className="text-gray-700 mb-6">{c.scoringIntro}</p>

            <div className="space-y-6">
              {c.scoringComponents.map((comp, idx) => {
                const colorMap: Record<string, { bg: string; text: string; badge: string; gradient: string }> = {
                  green: { bg: "bg-green-50", text: "text-green-700", badge: "bg-green-600", gradient: "from-green-50" },
                  blue: { bg: "bg-blue-50", text: "text-blue-700", badge: "bg-blue-600", gradient: "from-blue-50" },
                  purple: { bg: "bg-purple-50", text: "text-purple-700", badge: "bg-purple-600", gradient: "from-purple-50" },
                  yellow: { bg: "bg-yellow-50", text: "text-yellow-700", badge: "bg-yellow-600", gradient: "from-yellow-50" },
                  red: { bg: "bg-red-50", text: "text-red-700", badge: "bg-red-600", gradient: "from-red-50" },
                };
                const colors = colorMap[comp.color] || colorMap.blue;
                const borderColor = comp.color === "red" ? "border-red-300" : "border-gray-300";

                return (
                  <div key={idx} className={`border ${borderColor} rounded-lg p-5 bg-gradient-to-${isRtl ? "l" : "r"} ${colors.gradient} to-white`}>
                    <div className="flex items-center justify-between mb-3">
                      <h3 className={`text-xl font-bold ${colors.text}`}>{comp.name}</h3>
                      <span className={`${colors.badge} text-white px-3 py-1 rounded-full text-sm font-semibold`}>
                        {comp.weight}
                      </span>
                    </div>
                    <p className="text-gray-700 mb-3">{comp.description}</p>
                    <ul className={`list-disc list-inside space-y-1 text-gray-600 mb-3 ${isRtl ? "mr-4" : "ml-4"}`}>
                      {comp.ranges.map((r, i) => (
                        <li key={i}>{r}</li>
                      ))}
                    </ul>
                    {comp.formula && (
                      <div className="bg-gray-800 text-gray-100 p-3 rounded font-mono text-sm" dir="ltr">
                        {comp.formula}
                      </div>
                    )}
                  </div>
                );
              })}
            </div>

            {/* Total */}
            <div className="mt-8 bg-gradient-to-r from-indigo-100 to-purple-100 border-2 border-indigo-400 rounded-lg p-6">
              <h3 className="text-xl font-bold mb-3 text-indigo-900">{c.scoringTotalTitle}</h3>
              <div className="bg-gray-900 text-gray-100 p-4 rounded font-mono text-sm" dir="ltr">
                {c.scoringTotalFormula}
              </div>
              <p className="text-sm text-gray-600 mt-3">{c.scoringTotalNote}</p>
            </div>
          </section>

          {/* 3. Tiers */}
          <section id="tiers" className="bg-white rounded-lg shadow-md p-8 border border-gray-200 scroll-mt-8">
            <h2 className="text-3xl font-bold mb-6 text-gray-800 border-b-2 border-indigo-500 pb-3">
              {c.tiersTitle}
            </h2>
            <div className="grid md:grid-cols-2 gap-6">
              {c.tiers.map((tier) => {
                const colorMap: Record<string, { border: string; text: string; badge: string; bg: string; exBg: string; exText: string }> = {
                  purple: { border: "border-purple-400", text: "text-purple-700", badge: "bg-purple-600", bg: "from-purple-50", exBg: "bg-purple-100", exText: "text-purple-900" },
                  blue: { border: "border-blue-400", text: "text-blue-700", badge: "bg-blue-600", bg: "from-blue-50", exBg: "bg-blue-100", exText: "text-blue-900" },
                  gray: { border: "border-gray-400", text: "text-gray-700", badge: "bg-gray-600", bg: "from-gray-50", exBg: "bg-gray-100", exText: "text-gray-900" },
                  orange: { border: "border-orange-400", text: "text-orange-700", badge: "bg-orange-600", bg: "from-orange-50", exBg: "bg-orange-100", exText: "text-orange-900" },
                };
                const colors = colorMap[tier.color] || colorMap.gray;

                return (
                  <div key={tier.name} className={`border-2 ${colors.border} rounded-lg p-6 bg-gradient-to-br ${colors.bg} to-white`}>
                    <div className="flex items-center gap-3 mb-4">
                      <span className="text-4xl">{tier.emoji}</span>
                      <div>
                        <h3 className={`text-2xl font-bold ${colors.text}`}>{tier.name}</h3>
                        <span className={`inline-block ${colors.badge} text-white px-3 py-1 rounded-full text-sm font-semibold`}>
                          {tier.scoreRange}
                        </span>
                      </div>
                    </div>
                    <p className="text-gray-700 mb-3">{tier.description}</p>
                    {tier.examples.length > 0 && (
                      <div className={`${colors.exBg} p-3 rounded text-sm`}>
                        <ul className="text-gray-700 space-y-1 list-disc list-inside">
                          {tier.examples.map((ex, i) => (
                            <li key={i}>{ex}</li>
                          ))}
                        </ul>
                      </div>
                    )}
                  </div>
                );
              })}
            </div>
            <div className={`mt-6 bg-yellow-50 ${isRtl ? "border-r-4" : "border-l-4"} border-yellow-400 p-4 rounded`}>
              <p className="text-sm text-gray-700"><strong>{c.tiersNote}</strong></p>
            </div>
          </section>

          {/* 4. Wallet Types */}
          <section id="wallet-types" className="bg-white rounded-lg shadow-md p-8 border border-gray-200 scroll-mt-8">
            <h2 className="text-3xl font-bold mb-6 text-gray-800 border-b-2 border-green-500 pb-3">
              {c.walletTypesTitle}
            </h2>
            <p className="text-gray-700 mb-6">{c.walletTypesIntro}</p>

            <div className="space-y-4 mb-6">
              {c.walletTypeLayers.map((layer, i) => {
                const colorMap: Record<string, string> = { green: "border-green-500", blue: "border-blue-500", purple: "border-purple-500" };
                const textMap: Record<string, string> = { green: "text-green-700", blue: "text-blue-700", purple: "text-purple-700" };
                return (
                  <div key={i} className={`bg-white p-4 rounded ${isRtl ? "border-r-4" : "border-l-4"} ${colorMap[layer.color] || "border-gray-500"}`}>
                    <h4 className={`font-bold ${textMap[layer.color] || "text-gray-700"} mb-1`}>{layer.title}</h4>
                    <p className="text-gray-700 text-sm">{layer.description}</p>
                  </div>
                );
              })}
            </div>

            <div className="overflow-x-auto">
              <table className="w-full border-collapse border border-gray-300">
                <thead>
                  <tr className="bg-gray-100">
                    {c.walletTypeTableHeaders.map((h, i) => (
                      <th key={i} className={`border border-gray-300 px-4 py-3 ${isRtl ? "text-right" : "text-left"} font-bold`}>{h}</th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {c.walletTypeRows.map((row, i) => (
                    <tr key={row.type} className={i % 2 === 0 ? "bg-white" : "bg-gray-50"}>
                      <td className="border border-gray-300 px-4 py-3 font-semibold">{row.type}</td>
                      <td className="border border-gray-300 px-4 py-3">{row.description}</td>
                      <td className="border border-gray-300 px-4 py-3 text-sm">{row.examples}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </section>

          {/* 5. Personas */}
          <section id="personas" className="bg-white rounded-lg shadow-md p-8 border border-gray-200 scroll-mt-8">
            <h2 className="text-3xl font-bold mb-6 text-gray-800 border-b-2 border-pink-500 pb-3">
              {c.personasTitle}
            </h2>
            <p className="text-gray-700 mb-6">{c.personasIntro}</p>

            <div className="grid md:grid-cols-2 gap-5">
              {c.personas.map((p) => {
                const safeColors: Record<string, { border: string; bg: string }> = {
                  purple: { border: "border-purple-300", bg: "from-purple-50" },
                  indigo: { border: "border-indigo-300", bg: "from-indigo-50" },
                  blue: { border: "border-blue-300", bg: "from-blue-50" },
                  green: { border: "border-green-300", bg: "from-green-50" },
                  yellow: { border: "border-yellow-300", bg: "from-yellow-50" },
                  teal: { border: "border-teal-300", bg: "from-teal-50" },
                  cyan: { border: "border-cyan-300", bg: "from-cyan-50" },
                  red: { border: "border-red-300", bg: "from-red-50" },
                  orange: { border: "border-orange-300", bg: "from-orange-50" },
                  gray: { border: "border-gray-300", bg: "from-gray-50" },
                };
                const colors = safeColors[p.color] || safeColors.gray;

                return (
                  <div key={p.name} className={`border-2 ${colors.border} rounded-lg p-5 bg-gradient-to-br ${colors.bg} to-white hover:shadow-lg transition`}>
                    <div className="flex items-center gap-3 mb-3">
                      <span className="text-3xl">{p.emoji}</span>
                      <h3 className="text-lg font-bold text-gray-800">{p.name}</h3>
                    </div>
                    <p className="text-gray-700 text-sm mb-2">{p.condition}</p>
                    <span className="inline-block bg-gray-200 text-gray-800 px-2 py-1 rounded text-xs font-semibold">
                      {c.confidenceLabel}: {p.confidence}
                    </span>
                  </div>
                );
              })}
            </div>
          </section>

          {/* 6. Community Score */}
          <section id="community" className="bg-white rounded-lg shadow-md p-8 border border-gray-200 scroll-mt-8">
            <h2 className="text-3xl font-bold mb-6 text-gray-800 border-b-2 border-cyan-500 pb-3">
              {c.communityTitle}
            </h2>
            <p className="text-gray-700 mb-6">{c.communityIntro}</p>

            <div className="space-y-4 mb-8">
              {c.communityComponents.map((comp) => {
                const colorMap: Record<string, { border: string; badge: string; gradient: string }> = {
                  blue: { border: "border-blue-500", badge: "bg-blue-600", gradient: "from-blue-50" },
                  purple: { border: "border-purple-500", badge: "bg-purple-600", gradient: "from-purple-50" },
                  green: { border: "border-green-500", badge: "bg-green-600", gradient: "from-green-50" },
                  yellow: { border: "border-yellow-500", badge: "bg-yellow-600", gradient: "from-yellow-50" },
                  red: { border: "border-red-500", badge: "bg-red-600", gradient: "from-red-50" },
                };
                const colors = colorMap[comp.color] || colorMap.blue;

                return (
                  <div key={comp.name} className={`bg-gradient-to-${isRtl ? "l" : "r"} ${colors.gradient} to-white ${isRtl ? "border-r-4" : "border-l-4"} ${colors.border} p-5 rounded`}>
                    <div className="flex items-center justify-between mb-2">
                      <h3 className="text-lg font-bold text-gray-800">{comp.name}</h3>
                      <span className={`${colors.badge} text-white px-3 py-1 rounded-full text-sm font-semibold`}>
                        {comp.weight}
                      </span>
                    </div>
                    <p className="text-gray-700 text-sm">{comp.description}</p>
                  </div>
                );
              })}
            </div>

            <h3 className="text-xl font-bold mb-4 text-gray-800">{c.gradesTitle}</h3>
            <div className="overflow-x-auto">
              <table className="w-full border-collapse border border-gray-300">
                <thead>
                  <tr className="bg-gray-100">
                    {c.gradeTableHeaders.map((h, i) => (
                      <th key={i} className={`border border-gray-300 px-4 py-2 ${isRtl ? "text-right" : "text-left"}`}>{h}</th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {c.grades.map((g) => {
                    const bgMap: Record<string, string> = { green: "bg-green-50", blue: "bg-blue-50", yellow: "bg-yellow-50", orange: "bg-orange-50", red: "bg-red-50" };
                    const textMap: Record<string, string> = { green: "text-green-700", blue: "text-blue-700", yellow: "text-yellow-700", orange: "text-orange-700", red: "text-red-700" };
                    return (
                      <tr key={g.grade} className={bgMap[g.color] || "bg-gray-50"}>
                        <td className="border border-gray-300 px-4 py-2">{g.range}</td>
                        <td className={`border border-gray-300 px-4 py-2 font-bold ${textMap[g.color] || "text-gray-700"}`}>{g.grade}</td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          </section>

          {/* 7. Token Intelligence */}
          <section id="holdings" className="bg-white rounded-lg shadow-md p-8 border border-gray-200 scroll-mt-8">
            <h2 className="text-3xl font-bold mb-6 text-gray-800 border-b-2 border-teal-500 pb-3">
              {c.holdingsTitle}
            </h2>
            <p className="text-gray-700 mb-6">{c.holdingsIntro}</p>

            <div className="grid md:grid-cols-2 gap-4 mb-6">
              {c.tokenCategories.map((t) => {
                const bgMap: Record<string, string> = { blue: "from-blue-50", green: "from-green-50", purple: "from-purple-50", orange: "from-orange-50" };
                return (
                  <div key={t.name} className={`border border-gray-300 rounded-lg p-5 bg-gradient-to-br ${bgMap[t.color] || "from-gray-50"} to-white`}>
                    <h3 className="text-lg font-bold text-gray-800 mb-2">{t.icon} {t.name}</h3>
                    <p className="text-gray-700 text-sm">{t.description}</p>
                  </div>
                );
              })}
            </div>

            <div className="bg-indigo-50 border border-indigo-300 rounded-lg p-6">
              <h3 className="text-xl font-bold text-indigo-800 mb-4">{c.concentrationTitle}</h3>
              <ul className="space-y-2 text-gray-700">
                {c.concentrationMetrics.map((m, i) => (
                  <li key={i} dangerouslySetInnerHTML={{ __html: m }} />
                ))}
              </ul>
            </div>
          </section>

          {/* 8. Investment Intent */}
          <section id="intent" className="bg-white rounded-lg shadow-md p-8 border border-gray-200 scroll-mt-8">
            <h2 className="text-3xl font-bold mb-6 text-gray-800 border-b-2 border-orange-500 pb-3">
              {c.intentTitle}
            </h2>

            <div className="space-y-4 mb-8">
              {c.intentSignals.map((s) => {
                const colorMap: Record<string, { border: string; gradient: string }> = {
                  green: { border: "border-green-500", gradient: "from-green-50" },
                  blue: { border: "border-blue-500", gradient: "from-blue-50" },
                  purple: { border: "border-purple-500", gradient: "from-purple-50" },
                  yellow: { border: "border-yellow-500", gradient: "from-yellow-50" },
                  orange: { border: "border-orange-500", gradient: "from-orange-50" },
                  red: { border: "border-red-500", gradient: "from-red-50" },
                };
                const colors = colorMap[s.color] || colorMap.blue;
                return (
                  <div key={s.name} className={`bg-gradient-to-${isRtl ? "l" : "r"} ${colors.gradient} to-white ${isRtl ? "border-r-4" : "border-l-4"} ${colors.border} p-5 rounded`}>
                    <h3 className="font-bold text-gray-800 mb-1">{s.icon} {s.name}</h3>
                    <p className="text-gray-700 text-sm">{s.description}</p>
                  </div>
                );
              })}
            </div>

            <div className="bg-gradient-to-r from-indigo-100 to-blue-100 border-2 border-indigo-400 rounded-lg p-6">
              <h3 className="text-xl font-bold text-indigo-900 mb-4">{c.readinessTitle}</h3>
              <div className="space-y-3">
                {c.readinessLevels.map((lvl) => {
                  const badgeMap: Record<string, string> = { green: "bg-green-600", yellow: "bg-yellow-600", gray: "bg-gray-600" };
                  return (
                    <div key={lvl.level} className="flex items-center gap-3">
                      <span className={`${badgeMap[lvl.color] || "bg-gray-600"} text-white px-4 py-2 rounded-lg font-bold`}>{lvl.level}</span>
                      <p className="text-gray-700">{lvl.description}</p>
                    </div>
                  );
                })}
              </div>
            </div>
          </section>

          {/* 9. CSV Columns */}
          <section id="csv" className="bg-white rounded-lg shadow-md p-8 border border-gray-200 scroll-mt-8">
            <h2 className="text-3xl font-bold mb-6 text-gray-800 border-b-2 border-red-500 pb-3">
              {c.csvTitle}
            </h2>

            <div className="bg-blue-50 border border-blue-300 rounded-lg p-5 mb-6">
              <h3 className="font-bold text-blue-900 mb-3">{c.csvInputsTitle}</h3>
              <ul className="space-y-1 text-gray-700">
                {c.csvInputs.map(([col, desc]) => (
                  <li key={col}><strong>{col}</strong> &mdash; {desc}</li>
                ))}
              </ul>
            </div>

            <div className="space-y-4">
              {c.csvGroups.map((group) => (
                <div key={group.title} className="bg-white border border-gray-300 rounded p-4">
                  <h4 className="font-bold text-gray-800 mb-2">{group.title}:</h4>
                  <ul className={`text-sm text-gray-700 space-y-1 list-disc list-inside ${isRtl ? "mr-4" : "ml-4"}`}>
                    {group.items.map(([col, desc]) => (
                      <li key={col}><strong>{col}:</strong> {desc}</li>
                    ))}
                  </ul>
                </div>
              ))}
            </div>
          </section>

          {/* 10. Sanctions */}
          <section id="sanctions" className="bg-white rounded-lg shadow-md p-8 border border-gray-200 scroll-mt-8">
            <h2 className="text-3xl font-bold mb-6 text-gray-800 border-b-2 border-red-600 pb-3">
              {c.sanctionsTitle}
            </h2>

            <div className="grid md:grid-cols-3 gap-6 mb-6">
              {c.sanctionsSources.map((src) => {
                const colorMap: Record<string, { border: string; bg: string; text: string }> = {
                  blue: { border: "border-blue-400", bg: "bg-blue-50", text: "text-blue-700" },
                  yellow: { border: "border-yellow-400", bg: "bg-yellow-50", text: "text-yellow-700" },
                  purple: { border: "border-purple-400", bg: "bg-purple-50", text: "text-purple-700" },
                };
                const colors = colorMap[src.color] || colorMap.blue;
                return (
                  <div key={src.name} className={`border-2 ${colors.border} rounded-lg p-5 ${colors.bg} text-center`}>
                    <span className="text-3xl block mb-2">{src.emoji}</span>
                    <h3 className={`text-lg font-bold ${colors.text}`}>{src.name}</h3>
                    <p className="text-gray-600 text-sm mt-1">{src.description}</p>
                  </div>
                );
              })}
            </div>

            <div className="space-y-3">
              {c.sanctionsNotes.map((note, i) => {
                const colorMap: Record<string, { bg: string; border: string }> = {
                  green: { bg: "bg-green-50", border: "border-green-500" },
                  blue: { bg: "bg-blue-50", border: "border-blue-500" },
                  red: { bg: "bg-red-50", border: "border-red-500" },
                };
                const colors = colorMap[note.color] || colorMap.blue;
                return (
                  <div key={i} className={`${colors.bg} ${isRtl ? "border-r-4" : "border-l-4"} ${colors.border} p-4 rounded`}>
                    <p className="text-gray-700 text-sm" dangerouslySetInnerHTML={{ __html: note.text }} />
                  </div>
                );
              })}
            </div>
          </section>

          {/* 11. Risk Flags */}
          <section id="risk-flags" className="bg-white rounded-lg shadow-md p-8 border border-gray-200 scroll-mt-8">
            <h2 className="text-3xl font-bold mb-6 text-gray-800 border-b-2 border-gray-600 pb-3">
              {c.riskFlagsTitle}
            </h2>

            <h3 className="text-xl font-bold mb-4 text-gray-800">{c.walletFlagsTitle}</h3>
            <div className="space-y-3 mb-8">
              {c.walletFlags.map((f) => {
                const colorMap: Record<string, { gradient: string; border: string }> = {
                  red: { gradient: "from-red-50", border: "border-red-500" },
                  orange: { gradient: "from-orange-50", border: "border-orange-500" },
                  yellow: { gradient: "from-yellow-50", border: "border-yellow-500" },
                  blue: { gradient: "from-blue-50", border: "border-blue-500" },
                  purple: { gradient: "from-purple-50", border: "border-purple-500" },
                };
                const colors = colorMap[f.color] || colorMap.blue;
                return (
                  <div key={f.name} className={`bg-gradient-to-${isRtl ? "l" : "r"} ${colors.gradient} to-white ${isRtl ? "border-r-4" : "border-l-4"} ${colors.border} p-4 rounded`}>
                    <h4 className="font-bold text-gray-800">{f.icon} {f.name}</h4>
                    <p className="text-gray-700 text-sm">{f.description}</p>
                  </div>
                );
              })}
            </div>

            <h3 className="text-xl font-bold mb-4 text-gray-800">{c.communityFlagsTitle}</h3>
            <div className="overflow-x-auto">
              <table className="w-full border-collapse border border-gray-300">
                <thead>
                  <tr className="bg-gray-100">
                    {c.communityFlagHeaders.map((h, i) => (
                      <th key={i} className={`border border-gray-300 px-4 py-2 ${isRtl ? "text-right" : "text-left"} font-bold`}>{h}</th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {c.communityFlags.map((cf, i) => (
                    <tr key={cf.flag} className={i % 2 === 0 ? "bg-white" : "bg-gray-50"}>
                      <td className="border border-gray-300 px-4 py-2 font-semibold">{cf.flag}</td>
                      <td className="border border-gray-300 px-4 py-2 text-sm">{cf.description}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </section>

          {/* Footer */}
          <div className="mt-12 bg-gradient-to-r from-gray-100 to-gray-200 rounded-lg p-8 border border-gray-300 text-center">
            <p className="text-gray-500 text-xs">Wallet Intelligence System &copy; 2026</p>
          </div>
        </main>
      </div>
    </div>
  );
}
