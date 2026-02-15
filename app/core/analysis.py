import time
from datetime import datetime, timezone
from . import rpc, chains, scoring
from .config import settings
from . import sanctions_service
from . import token_intelligence
from . import intent_signals


def run_wallet_analysis(address: str, chain: str, effective_settings: dict | None = None) -> dict:
    """
    Performs the full two-pass analysis for a single wallet.
    """
    start_time = time.time()

    # --- Initial Setup & Pass A (Cheap) ---
    chain_config = chains.get_chain_config(chain)
    is_evm = chain != "solana"

    native_balance = 0.0
    is_contract = False
    tx_count = 0
    stable_balances = []

    if is_evm:
        w3 = rpc.get_w3_instance(chain)
        native_balance = rpc.get_evm_native_balance(w3, address)
        is_contract = rpc.is_evm_contract(w3, address)
        tx_count = rpc.get_evm_tx_count(w3, address)
        for symbol, token_addr in chain_config.get("stables", {}).items():
            bal = rpc.get_evm_token_balance(w3, address, token_addr)
            if bal > 0:
                stable_balances.append({"symbol": symbol, "address": token_addr, "amount": bal})
    else:  # Solana
        client = rpc.get_solana_client(chain)
        native_balance = rpc.get_sol_native_balance(client, address)
        is_contract = rpc.is_solana_contract(client, address)
        tx_count = rpc.get_sol_tx_count(client, address)
        for symbol, token_addr in chain_config.get("stables", {}).items():
            bal = rpc.get_sol_token_balance(client, address, token_addr)
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

    # --- Pass B (Top Tokens for wallets with some value) ---
    top_token_balances = []
    staked_token_balances = []
    governance_token_balances = []
    est_net_worth_usd = native_balance_usd + total_stable_usd

    if est_net_worth_usd >= 100 or tx_count >= 10:
        # Top tokens (general)
        top_tokens_config = chain_config.get("top_tokens", {})
        if top_tokens_config:
            if is_evm:
                for symbol, token_addr in top_tokens_config.items():
                    bal = rpc.get_evm_token_balance(w3, address, token_addr)
                    if bal > 0:
                        top_token_balances.append({"symbol": symbol, "address": token_addr, "amount": bal})
            else:
                for symbol, token_addr in top_tokens_config.items():
                    bal = rpc.get_sol_token_balance(client, address, token_addr)
                    if bal > 0:
                        top_token_balances.append({"symbol": symbol, "address": token_addr, "amount": bal})

        # Staked tokens
        staked_tokens_config = chain_config.get("staked_tokens", {})
        if staked_tokens_config:
            if is_evm:
                for symbol, token_addr in staked_tokens_config.items():
                    bal = rpc.get_evm_token_balance(w3, address, token_addr)
                    if bal > 0:
                        usd_val = float(bal) * native_price_usd  # staked tokens ~= native price
                        staked_token_balances.append({"symbol": symbol, "address": token_addr, "amount": bal, "usd": usd_val})
                        est_net_worth_usd += usd_val
            else:
                for symbol, token_addr in staked_tokens_config.items():
                    bal = rpc.get_sol_token_balance(client, address, token_addr)
                    if bal > 0:
                        usd_val = float(bal) * native_price_usd
                        staked_token_balances.append({"symbol": symbol, "address": token_addr, "amount": bal, "usd": usd_val})
                        est_net_worth_usd += usd_val

        # Governance tokens (no easy price — use 0 for now, count matters more than value)
        governance_tokens_config = chain_config.get("governance_tokens", {})
        if governance_tokens_config:
            if is_evm:
                for symbol, token_addr in governance_tokens_config.items():
                    bal = rpc.get_evm_token_balance(w3, address, token_addr)
                    if bal > 0:
                        governance_token_balances.append({"symbol": symbol, "address": token_addr, "amount": bal, "usd": 0})
            else:
                for symbol, token_addr in governance_tokens_config.items():
                    bal = rpc.get_sol_token_balance(client, address, token_addr)
                    if bal > 0:
                        governance_token_balances.append({"symbol": symbol, "address": token_addr, "amount": bal, "usd": 0})

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
    sanctions_enabled = True  # default
    if effective_settings:
        sanctions_enabled = effective_settings.get("sanctions", {}).get("enabled", True)
    if sanctions_enabled:
        sanctions_result = sanctions_service.check_address(address)

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

    # --- Behavioral & Risk Signals ---
    activity_indicators = {
        "tx_count": tx_count,
        "top_tokens": top_token_balances,
        "protocols_used": [],
        "cross_chain_activity": False,
        "recent_active_days": -1,
    }

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
