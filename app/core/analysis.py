import time
from datetime import datetime, timezone
from concurrent.futures import ThreadPoolExecutor, as_completed
from . import rpc, chains, scoring
from .config import settings
from . import sanctions_service
from . import token_intelligence
from . import intent_signals
from . import wallet_identity
import logging

logger = logging.getLogger(__name__)


def _fetch_token_balance(is_evm, w3_or_client, address, symbol, token_addr):
    """Fetch a single token balance (runs in thread pool)."""
    if is_evm:
        bal = rpc.get_evm_token_balance(w3_or_client, address, token_addr)
    else:
        bal = rpc.get_sol_token_balance(w3_or_client, address, token_addr)
    return symbol, token_addr, bal


def run_wallet_analysis(address: str, chain: str, effective_settings: dict | None = None) -> dict:
    """
    Performs the full two-pass analysis for a single wallet.
    Uses parallel RPC calls for speed.
    """
    start_time = time.time()

    # --- Initial Setup & Pass A (Parallel RPC calls) ---
    chain_config = chains.get_chain_config(chain)
    is_evm = chain != "solana"

    native_balance = 0.0
    is_contract = False
    tx_count = 0
    stable_balances = []

    if is_evm:
        w3 = rpc.get_w3_instance(chain)
        w3_or_client = w3
        rpc_url = chain_config["rpc_url"]

        # Pass A fast path: 2 HTTP requests instead of N serial/parallel calls.
        # batch_evm_core_calls sends balance+code+txcount in one JSON-RPC batch.
        # multicall3_erc20_balances fetches all stablecoin balances in one eth_call.
        try:
            native_balance, is_contract, tx_count = rpc.batch_evm_core_calls(rpc_url, address)
            stable_balances = rpc.multicall3_erc20_balances(w3, address, chain_config.get("stables", {}))
        except Exception as e:
            # Fallback: provider doesn't support JSON-RPC batch — run calls in parallel
            logger.warning(f"Batch RPC failed for {address} on {chain}, falling back: {e}")
            with ThreadPoolExecutor(max_workers=8) as executor:
                future_balance  = executor.submit(rpc.get_evm_native_balance, w3, address)
                future_contract = executor.submit(rpc.is_evm_contract,        w3, address)
                future_tx_count = executor.submit(rpc.get_evm_tx_count,       w3, address)
                stable_futures = {
                    executor.submit(rpc.get_evm_token_balance, w3, address, token_addr): (symbol, token_addr)
                    for symbol, token_addr in chain_config.get("stables", {}).items()
                }
                native_balance = future_balance.result()
                is_contract    = future_contract.result()
                tx_count       = future_tx_count.result()
                for f, (symbol, token_addr) in stable_futures.items():
                    bal = f.result()
                    if bal > 0:
                        stable_balances.append({"symbol": symbol, "address": token_addr, "amount": bal})

    else:  # Solana
        client = rpc.get_solana_client(chain)
        w3_or_client = client

        with ThreadPoolExecutor(max_workers=8) as executor:
            future_balance = executor.submit(rpc.get_sol_native_balance, client, address)
            future_contract = executor.submit(rpc.is_solana_contract, client, address)
            future_tx_count = executor.submit(rpc.get_sol_tx_count, client, address)

            stable_futures = {}
            for symbol, token_addr in chain_config.get("stables", {}).items():
                f = executor.submit(rpc.get_sol_token_balance, client, address, token_addr)
                stable_futures[f] = (symbol, token_addr)

            native_balance = future_balance.result()
            is_contract = future_contract.result()
            tx_count = future_tx_count.result()

            for f, (symbol, token_addr) in stable_futures.items():
                bal = f.result()
                if bal > 0:
                    stable_balances.append({"symbol": symbol, "address": token_addr, "amount": bal})

    # --- Price Fetching ---
    coingecko_ids_to_fetch = {chain_config["coingecko_id"]}
    prices = rpc.get_token_prices(tuple(coingecko_ids_to_fetch))
    native_price_usd = prices.get(chain_config["coingecko_id"], 0)

    # --- Financial Profile (Pass A) ---
    native_balance_usd = float(native_balance) * native_price_usd
    total_stable_usd = sum(float(b['amount']) for b in stable_balances)

    for b in stable_balances:
        b['usd'] = b['amount']  # 1:1 peg assumption

    # --- Pass B (Token Discovery — Alchemy API or fallback) ---
    top_token_balances = []
    staked_token_balances = []
    governance_token_balances = []
    all_discovered_tokens = []
    est_net_worth_usd = native_balance_usd + total_stable_usd

    if est_net_worth_usd >= 100 or tx_count >= 10:
        # Build lookup sets from known token configs for classification
        staked_addrs = {v.lower(): k for k, v in chain_config.get("staked_tokens", {}).items()}
        gov_addrs = {v.lower(): k for k, v in chain_config.get("governance_tokens", {}).items()}
        stable_addrs = {v.lower() for v in chain_config.get("stables", {}).values()}
        top_addrs = {v.lower(): k for k, v in chain_config.get("top_tokens", {}).items()}

        # Try Alchemy Token Discovery API (EVM only, single call for all tokens)
        discovered = []
        if is_evm and chain_config.get("rpc_url"):
            discovered = rpc.discover_evm_tokens(chain_config["rpc_url"], address, max_tokens=30)

        if discovered:
            # Classify discovered tokens
            for token in discovered:
                addr_lower = token["contract_address"].lower()

                # Skip stablecoins — already counted in Pass A
                if addr_lower in stable_addrs:
                    continue

                entry = {
                    "symbol": token["symbol"],
                    "address": token["contract_address"],
                    "amount": token["amount"],
                    "name": token.get("name", token["symbol"]),
                }

                if addr_lower in staked_addrs:
                    usd_val = float(token["amount"]) * native_price_usd
                    entry["usd"] = usd_val
                    staked_token_balances.append(entry)
                    est_net_worth_usd += usd_val
                elif addr_lower in gov_addrs:
                    entry["usd"] = 0
                    governance_token_balances.append(entry)
                elif addr_lower in top_addrs:
                    top_token_balances.append(entry)
                else:
                    # Unknown token — still valuable intel for investor profiling
                    top_token_balances.append(entry)

            # Price all non-stablecoin, non-staked tokens via DeFiLlama (free, no API key)
            if top_token_balances and is_evm:
                token_addrs = tuple(t["address"].lower() for t in top_token_balances)
                llama_prices = rpc.get_token_prices_by_address(chain, token_addrs)
                for token in top_token_balances:
                    price = llama_prices.get(token["address"].lower(), 0)
                    token["usd"] = round(float(token["amount"]) * price, 2)
                    est_net_worth_usd += token["usd"]

            all_discovered_tokens = discovered
            logger.info(f"Alchemy discovered {len(discovered)} tokens for {address}: "
                       f"{len(top_token_balances)} top, {len(staked_token_balances)} staked, "
                       f"{len(governance_token_balances)} governance")

        else:
            # Fallback: use hardcoded token list with parallel checks
            top_tokens_config = chain_config.get("top_tokens", {})
            staked_tokens_config = chain_config.get("staked_tokens", {})
            governance_tokens_config = chain_config.get("governance_tokens", {})

            with ThreadPoolExecutor(max_workers=12) as executor:
                top_futures = {}
                staked_futures = {}
                gov_futures = {}

                for symbol, token_addr in top_tokens_config.items():
                    f = executor.submit(_fetch_token_balance, is_evm, w3_or_client, address, symbol, token_addr)
                    top_futures[f] = True
                for symbol, token_addr in staked_tokens_config.items():
                    f = executor.submit(_fetch_token_balance, is_evm, w3_or_client, address, symbol, token_addr)
                    staked_futures[f] = True
                for symbol, token_addr in governance_tokens_config.items():
                    f = executor.submit(_fetch_token_balance, is_evm, w3_or_client, address, symbol, token_addr)
                    gov_futures[f] = True

                for f in top_futures:
                    symbol, token_addr, bal = f.result()
                    if bal > 0:
                        top_token_balances.append({"symbol": symbol, "address": token_addr, "amount": bal, "usd": 0})
                for f in staked_futures:
                    symbol, token_addr, bal = f.result()
                    if bal > 0:
                        usd_val = float(bal) * native_price_usd
                        staked_token_balances.append({"symbol": symbol, "address": token_addr, "amount": bal, "usd": usd_val})
                        est_net_worth_usd += usd_val
                for f in gov_futures:
                    symbol, token_addr, bal = f.result()
                    if bal > 0:
                        governance_token_balances.append({"symbol": symbol, "address": token_addr, "amount": bal, "usd": 0})

                # Price fallback top tokens via DeFiLlama
                if top_token_balances and is_evm:
                    token_addrs = tuple(t["address"].lower() for t in top_token_balances)
                    llama_prices = rpc.get_token_prices_by_address(chain, token_addrs)
                    for token in top_token_balances:
                        price = llama_prices.get(token["address"].lower(), 0)
                        token["usd"] = round(float(token["amount"]) * price, 2)
                        est_net_worth_usd += token["usd"]

    # --- Token Intelligence ---
    token_intel = token_intelligence.analyze_token_holdings(
        native_balance_usd=native_balance_usd,
        stable_balances=stable_balances,
        top_token_balances=top_token_balances,
        staked_token_balances=staked_token_balances,
        governance_token_balances=governance_token_balances,
    )

    # --- Identity & Labeling ---
    labels = []
    known_entity_type = "user"
    confidence = 0.5
    label_types = chains.get_label_types_for_address(chain, address)
    known_label = chains.get_known_label(chain, address)
    wallet_type = chains.get_wallet_type(chain, address, is_contract=is_contract)

    # Balance heuristic: EOA wallets with very large balances and/or high activity
    # are almost certainly institutional custodians (exchange hot wallets, market makers).
    # No individual investor holds $10M+ in a single EOA with thousands of transactions.
    if wallet_type == "USER" and not is_contract and not known_label:
        if est_net_worth_usd >= 10_000_000 and tx_count >= 1000:
            wallet_type = "CEX_EXCHANGE"
            labels.append("Large Institutional Wallet")
            confidence = 0.80
        elif est_net_worth_usd >= 50_000_000:
            wallet_type = "CEX_EXCHANGE"
            labels.append("Very Large Institutional Wallet")
            confidence = 0.85

    if known_label:
        known_entity_type = known_label['type']
        labels.append(known_label['name'])
        confidence = known_label.get('confidence', 0.95)
    elif is_contract:
        known_entity_type = "contract"
        labels.append("Smart Contract")
        confidence = 0.9
    elif tx_count == 0 and est_net_worth_usd > 10:
        labels.append("Inactive Holder")
        confidence = 0.7
    elif tx_count > 1000:
        labels.append("High Activity")
        confidence = 0.6

    # --- Sanctions Check ---
    sanctions_result = None
    sanctions_check_error = False
    sanctions_enabled = True  # default
    if effective_settings:
        sanctions_enabled = effective_settings.get("sanctions", {}).get("enabled", True)
    if sanctions_enabled:
        try:
            sanctions_result = sanctions_service.check_address(address)
        except sanctions_service.SanctionsCheckError:
            # C5: DB error during sanctions check — flag as inconclusive rather than clean
            sanctions_check_error = True
            logger.warning(f"Sanctions check inconclusive for {address} due to DB error")

    # --- New Multi-Component Scoring ---
    scoring_settings = None
    if effective_settings:
        scoring_settings = effective_settings.get("scoring")

    score_result = scoring.score_wallet(
        est_net_worth_usd=est_net_worth_usd,
        stable_usd_total=total_stable_usd,
        tx_count=tx_count,
        is_contract=is_contract,
        known_entity_type=known_entity_type,
        labels=labels,
        label_types=label_types,
        top_token_count=len(top_token_balances) + len(staked_token_balances) + len(governance_token_balances),
        scoring_settings=scoring_settings,
        token_intel=token_intel,
    )

    # --- Investment Intent Signals ---
    wallet_intent_signals = intent_signals.detect_intent_signals(
        token_intel=token_intel,
        tx_count=tx_count,
        persona=score_result["persona"],
        tier=score_result["tier"],
    )

    # --- Identity Enrichment (ENS, wallet age, country signal, NFT) ---
    # Calls run in parallel inside enrich_wallet_identity; small wallets are skipped.
    identity_data = wallet_identity.enrich_wallet_identity(
        address=address,
        chain=chain,
        rpc_url=chain_config.get("rpc_url"),
        w3=w3_or_client if is_evm else None,
        wallet_type=wallet_type,
        est_net_worth_usd=est_net_worth_usd,
        tx_count=tx_count,
    )
    # ENS name goes first in labels so it's visible in reports
    if identity_data.get("ens_name"):
        labels.insert(0, identity_data["ens_name"])

    # --- Behavioral & Risk Signals ---
    activity_indicators = {
        "tx_count": tx_count,
        "top_tokens": top_token_balances,
        "protocols_used": [],
        "cross_chain_activity": False,
        "recent_active_days": -1,
    }
    # Merge identity enrichment into activity_indicators (no DB schema change needed)
    if identity_data:
        activity_indicators.update(identity_data)

    risk_flags = []
    if wallet_type in ("CEX_EXCHANGE", "DEX_ROUTER", "BRIDGE", "PROTOCOL", "CONTRACT"):
        risk_flags.append("INFRASTRUCTURE_WALLET")
    if is_contract and tx_count == 0:
        risk_flags.append("UNVERIFIED_OR_UNUSED_CONTRACT")
    if score_result["sybil_risk_score"] >= 50:
        risk_flags.append("SYBIL_RISK")
    elif score_result["sybil_risk_score"] >= 30:
        risk_flags.append("LOW_VALUE_HIGH_ACTIVITY")
    if sanctions_result:
        risk_flags.append("SANCTIONS_HIT")
    if sanctions_check_error:
        risk_flags.append("SANCTIONS_CHECK_INCONCLUSIVE")

    end_time = time.time()
    notes = f"Analysis completed in {end_time - start_time:.2f}s."

    return {
        "address": address,
        "chain": chain,
        "tier": score_result["tier"],
        "is_contract": str(is_contract),
        "known_entity_type": known_entity_type,
        "labels": labels,
        "confidence": confidence,
        "native_balance": native_balance,
        "stable_balances": stable_balances,
        "est_net_worth_usd": round(est_net_worth_usd, 2),
        "activity_indicators": activity_indicators,
        "product_relevance_score": score_result["product_relevance_score"],
        "risk_flags": risk_flags,
        "notes": notes,
        "last_scored_at": datetime.now(timezone.utc),
        # Scoring fields
        "investor_score": score_result["investor_score"],
        "balance_score": score_result["balance_score"],
        "activity_score": score_result["activity_score"],
        "defi_investor_score": score_result["defi_investor_score"],
        "reputation_score": score_result["reputation_score"],
        "sybil_risk_score": score_result["sybil_risk_score"],
        "persona": score_result["persona"],
        "wallet_type": wallet_type,
        # Sanctions fields
        "sanctions_hit": bool(sanctions_result),
        "sanctions_list_name": sanctions_result["list_name"] if sanctions_result else None,
        "sanctions_entity_name": sanctions_result["entity_name"] if sanctions_result else None,
        # Intelligence fields
        "token_intelligence": token_intel,
        "persona_detail": score_result["persona_detail"],
        "intent_signals": wallet_intent_signals,
        "staked_balances": staked_token_balances,
        "governance_balances": governance_token_balances,
    }
