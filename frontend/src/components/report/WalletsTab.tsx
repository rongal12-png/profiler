"use client";

import { useState, useMemo } from "react";
import type { WalletRecord } from "@/lib/types";
import { truncateAddress, formatUsd, formatPct } from "@/lib/aggregates";
import Badge, { TierBadge, ReadinessBadge } from "@/components/ui/Badge";
import ProgressBar from "@/components/ui/ProgressBar";

interface Props {
  wallets: WalletRecord[];
}

type SortKey = "investor_score" | "est_net_worth_usd" | "tx_count" | "address" | "tier" | "persona";

const PAGE_SIZE = 25;

export default function WalletsTab({ wallets }: Props) {
  const [search, setSearch] = useState("");
  const [tierFilter, setTierFilter] = useState("all");
  const [typeFilter, setTypeFilter] = useState("all");
  const [chainFilter, setChainFilter] = useState("all");
  const [sortKey, setSortKey] = useState<SortKey>("investor_score");
  const [sortAsc, setSortAsc] = useState(false);
  const [page, setPage] = useState(0);
  const [expandedAddr, setExpandedAddr] = useState<string | null>(null);

  const tiers = useMemo(() => [...new Set(wallets.map((w) => w.tier))].sort(), [wallets]);
  const types = useMemo(() => [...new Set(wallets.map((w) => w.wallet_type))].sort(), [wallets]);
  // Build chain options from scan_chains (may be comma-separated for multi-chain wallets)
  const chains = useMemo(() => {
    const all = new Set<string>();
    wallets.forEach((w) => {
      (w.scan_chains || w.chain || "").split(",").forEach((c) => { const t = c.trim(); if (t) all.add(t); });
    });
    return [...all].sort();
  }, [wallets]);

  const filtered = useMemo(() => {
    let result = wallets;
    if (search) {
      const q = search.toLowerCase();
      result = result.filter((w) => w.address.toLowerCase().includes(q));
    }
    if (tierFilter !== "all") result = result.filter((w) => w.tier === tierFilter);
    if (typeFilter !== "all") result = result.filter((w) => w.wallet_type === typeFilter);
    if (chainFilter !== "all") result = result.filter((w) =>
      (w.scan_chains || w.chain || "").split(",").map((c) => c.trim()).includes(chainFilter)
    );

    result = [...result].sort((a, b) => {
      const av = a[sortKey] ?? 0;
      const bv = b[sortKey] ?? 0;
      if (typeof av === "string" && typeof bv === "string") return sortAsc ? av.localeCompare(bv) : bv.localeCompare(av);
      return sortAsc ? (av as number) - (bv as number) : (bv as number) - (av as number);
    });
    return result;
  }, [wallets, search, tierFilter, typeFilter, chainFilter, sortKey, sortAsc]);

  const totalPages = Math.ceil(filtered.length / PAGE_SIZE);
  const pageWallets = filtered.slice(page * PAGE_SIZE, (page + 1) * PAGE_SIZE);

  function handleSort(key: SortKey) {
    if (sortKey === key) setSortAsc(!sortAsc);
    else { setSortKey(key); setSortAsc(false); }
  }

  const SortHeader = ({ label, field }: { label: string; field: SortKey }) => (
    <th
      className="px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer hover:text-gray-700 select-none"
      onClick={() => handleSort(field)}
    >
      {label} {sortKey === field ? (sortAsc ? "↑" : "↓") : ""}
    </th>
  );

  return (
    <div className="space-y-4">
      {/* Filters */}
      <div className="flex flex-wrap gap-3">
        <input
          type="text"
          placeholder="Search address..."
          value={search}
          onChange={(e) => { setSearch(e.target.value); setPage(0); }}
          className="px-3 py-1.5 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none w-64"
        />
        <select value={tierFilter} onChange={(e) => { setTierFilter(e.target.value); setPage(0); }} className="px-3 py-1.5 border border-gray-300 rounded-lg text-sm bg-white">
          <option value="all">All Tiers</option>
          {tiers.map((t) => <option key={t} value={t}>{t}</option>)}
        </select>
        <select value={typeFilter} onChange={(e) => { setTypeFilter(e.target.value); setPage(0); }} className="px-3 py-1.5 border border-gray-300 rounded-lg text-sm bg-white">
          <option value="all">All Types</option>
          {types.map((t) => <option key={t} value={t}>{t}</option>)}
        </select>
        <select value={chainFilter} onChange={(e) => { setChainFilter(e.target.value); setPage(0); }} className="px-3 py-1.5 border border-gray-300 rounded-lg text-sm bg-white">
          <option value="all">All Chains</option>
          {chains.map((c) => <option key={c} value={c}>{c}</option>)}
        </select>
        <span className="text-xs text-gray-400 self-center">{filtered.length} wallets</span>
      </div>

      {/* Table */}
      <div className="overflow-x-auto border border-gray-200 rounded-xl">
        <table className="min-w-full divide-y divide-gray-200">
          <thead className="bg-gray-50">
            <tr>
              <SortHeader label="Address" field="address" />
              <th className="px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase">Chains</th>
              <SortHeader label="Tier" field="tier" />
              <th className="px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase">Type</th>
              <SortHeader label="Persona" field="persona" />
              <SortHeader label="Score" field="investor_score" />
              <SortHeader label="Net Worth" field="est_net_worth_usd" />
              <SortHeader label="Txns" field="tx_count" />
              <th className="px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase">Risk</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-100 bg-white">
            {pageWallets.map((w) => (
              <WalletRow
                key={w.address}
                wallet={w}
                expanded={expandedAddr === w.address}
                onToggle={() => setExpandedAddr(expandedAddr === w.address ? null : w.address)}
              />
            ))}
          </tbody>
        </table>
      </div>

      {/* Pagination */}
      {totalPages > 1 && (
        <div className="flex items-center justify-between">
          <button
            onClick={() => setPage(Math.max(0, page - 1))}
            disabled={page === 0}
            className="px-3 py-1.5 text-sm border border-gray-300 rounded-lg disabled:opacity-40 hover:bg-gray-50"
          >
            Previous
          </button>
          <span className="text-sm text-gray-500">
            Page {page + 1} of {totalPages}
          </span>
          <button
            onClick={() => setPage(Math.min(totalPages - 1, page + 1))}
            disabled={page >= totalPages - 1}
            className="px-3 py-1.5 text-sm border border-gray-300 rounded-lg disabled:opacity-40 hover:bg-gray-50"
          >
            Next
          </button>
        </div>
      )}
    </div>
  );
}

function WalletRow({ wallet: w, expanded, onToggle }: { wallet: WalletRecord; expanded: boolean; onToggle: () => void }) {
  return (
    <>
      <tr className="hover:bg-gray-50 cursor-pointer" onClick={onToggle}>
        <td className="px-3 py-2.5 text-sm font-mono text-blue-600">{truncateAddress(w.address)}</td>
        <td className="px-3 py-2.5 text-sm text-gray-600 whitespace-nowrap" title={w.scan_chains || w.chain}>
          {w.scan_chains && w.scan_chains !== w.chain
            ? <span>{w.scan_chains.split(",").length} chains</span>
            : <span>{w.chain}</span>}
        </td>
        <td className="px-3 py-2.5"><TierBadge tier={w.tier} /></td>
        <td className="px-3 py-2.5">
          <Badge label={w.wallet_type.replace(/_/g, " ")} color={w.wallet_type === "USER" ? "blue" : "gray"} />
        </td>
        <td className="px-3 py-2.5 text-sm text-gray-700">{w.persona}</td>
        <td className="px-3 py-2.5 text-sm font-medium text-gray-900">{w.investor_score.toFixed(1)}</td>
        <td className="px-3 py-2.5 text-sm text-gray-700">{formatUsd(w.est_net_worth_usd)}</td>
        <td className="px-3 py-2.5 text-sm text-gray-500">{w.tx_count}</td>
        <td className="px-3 py-2.5">
          {w.sanctions_hit && <Badge label="SANCTIONED" color="red" />}
          {w.sybil_risk_score >= 40 && <Badge label="Sybil" color="yellow" />}
        </td>
      </tr>
      {expanded && <ExpandedRow wallet={w} />}
    </>
  );
}

function ExpandedRow({ wallet: w }: { wallet: WalletRecord }) {
  const scores = [
    { label: "Balance", value: w.balance_score, color: "bg-blue-500" },
    { label: "Activity", value: w.activity_score, color: "bg-indigo-500" },
    { label: "DeFi", value: w.defi_investor_score, color: "bg-cyan-500" },
    { label: "Reputation", value: w.reputation_score, color: "bg-teal-500" },
    { label: "Sybil Risk", value: w.sybil_risk_score, color: "bg-red-400" },
  ];

  return (
    <tr>
      <td colSpan={9} className="px-3 py-4 bg-gray-50">
        {/* Multi-chain summary */}
        {w.scan_chains && w.scan_chains !== w.chain && (
          <div className="mb-3 flex flex-wrap gap-3 text-xs text-gray-600">
            <span><span className="font-medium">Scanned:</span> {w.scan_chains}</span>
            {w.chains_with_assets && (
              <span><span className="font-medium">Has funds on:</span> {w.chains_with_assets || "—"}</span>
            )}
            <span><span className="font-medium">Combined net worth:</span> {formatUsd(w.est_net_worth_usd)}</span>
          </div>
        )}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {/* Scores */}
          <div>
            <h4 className="text-xs font-semibold text-gray-500 uppercase mb-3">Score Breakdown</h4>
            <div className="space-y-2">
              {scores.map((s) => (
                <ProgressBar key={s.label} value={s.value} label={s.label} showPct color={s.color} />
              ))}
            </div>
          </div>

          {/* Persona Detail */}
          <div>
            <h4 className="text-xs font-semibold text-gray-500 uppercase mb-3">Persona</h4>
            {w.persona_detail ? (
              <div className="space-y-2">
                <div className="flex items-center gap-2">
                  <span className="font-medium text-sm text-gray-800">{w.persona_detail.primary}</span>
                  <span className="text-xs text-gray-400">({(w.persona_detail.confidence * 100).toFixed(0)}% confidence)</span>
                </div>
                {w.persona_detail.secondary && (
                  <p className="text-xs text-gray-500">Secondary: {w.persona_detail.secondary}</p>
                )}
                <ul className="text-xs text-gray-500 space-y-0.5">
                  {w.persona_detail.evidence.map((e, i) => (
                    <li key={i} className="flex items-start gap-1">
                      <span className="text-gray-400 mt-px">&#8226;</span>
                      {e}
                    </li>
                  ))}
                </ul>
              </div>
            ) : (
              <p className="text-sm text-gray-400">{w.persona}</p>
            )}

            {/* Intent Signals */}
            {w.intent_signals && w.intent_signals.signals.length > 0 && (
              <div className="mt-4">
                <div className="flex items-center gap-2 mb-2">
                  <span className="text-xs font-semibold text-gray-500 uppercase">Intent</span>
                  <ReadinessBadge readiness={w.intent_signals.investment_readiness} />
                </div>
                <ul className="text-xs text-gray-500 space-y-1">
                  {w.intent_signals.signals.map((s, i) => (
                    <li key={i} className="flex items-start gap-1">
                      <Badge label={s.strength} color={s.strength === "strong" ? "green" : s.strength === "moderate" ? "yellow" : "gray"} className="text-[10px] px-1.5" />
                      <span>{s.detail}</span>
                    </li>
                  ))}
                </ul>
              </div>
            )}
          </div>

          {/* Token Intelligence */}
          <div>
            <h4 className="text-xs font-semibold text-gray-500 uppercase mb-3">Token Holdings</h4>
            {w.token_intelligence ? (
              <div className="space-y-2">
                {Object.entries(w.token_intelligence.categories).map(([cat, data]) => (
                  data.pct > 0 && (
                    <ProgressBar
                      key={cat}
                      value={data.pct * 100}
                      label={`${cat} (${formatUsd(data.usd)})`}
                      showPct
                      color={cat === "native" ? "bg-blue-500" : cat === "stablecoin" ? "bg-green-500" : cat === "staked" ? "bg-indigo-500" : cat === "governance" ? "bg-violet-500" : "bg-gray-400"}
                    />
                  )
                ))}
                <div className="flex gap-2 mt-2 flex-wrap">
                  {w.token_intelligence.dry_powder_signal && <Badge label="Dry Powder" color="green" />}
                  {w.token_intelligence.long_term_signal && <Badge label="Long Term" color="indigo" />}
                  {w.token_intelligence.has_staking_positions && <Badge label="Staker" color="cyan" />}
                  {w.token_intelligence.has_governance_tokens && <Badge label="Governance" color="orange" />}
                </div>
              </div>
            ) : (
              <p className="text-sm text-gray-400">No token data</p>
            )}
          </div>
        </div>
      </td>
    </tr>
  );
}
