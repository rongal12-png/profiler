"""
Wallet identity enrichment: ENS names, on-chain identity, country/geographic signals,
NFT holdings, and wallet age detection.

All functions fail silently and return empty dicts — they are best-effort enrichments
and must not block the core analysis pipeline.
"""
import logging
import requests
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone

# Simple ENS reverse-lookup cache (address → name, ttl = 1hr)
# ENS names almost never change, so a long TTL is safe.
_ENS_CACHE: dict[str, tuple[str | None, float]] = {}
_ENS_CACHE_TTL = 3600  # 1 hour

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# CEX → Geographic signal mapping
# Key must match label_name values in known_labels.json exactly.
# Confidence: 0.0–1.0 (how strongly this CEX implies the country hint)
# ---------------------------------------------------------------------------
CEX_COUNTRY_SIGNALS: dict[str, dict] = {
    # North America
    "Coinbase":        {"region": "North America",      "country_hint": "United States",    "confidence": 0.65},
    "Coinbase 2":      {"region": "North America",      "country_hint": "United States",    "confidence": 0.65},
    "Coinbase 3":      {"region": "North America",      "country_hint": "United States",    "confidence": 0.65},
    "Coinbase 4":      {"region": "North America",      "country_hint": "United States",    "confidence": 0.65},
    "Coinbase 5":      {"region": "North America",      "country_hint": "United States",    "confidence": 0.65},
    "Coinbase Prime":  {"region": "North America",      "country_hint": "United States",    "confidence": 0.70},
    "Gemini":          {"region": "North America",      "country_hint": "United States",    "confidence": 0.70},
    "Gemini 2":        {"region": "North America",      "country_hint": "United States",    "confidence": 0.70},
    "Gemini 3":        {"region": "North America",      "country_hint": "United States",    "confidence": 0.70},
    "Kraken":          {"region": "North America / EU", "country_hint": "US / EU",          "confidence": 0.50},
    "Kraken 2":        {"region": "North America / EU", "country_hint": "US / EU",          "confidence": 0.50},
    "Kraken 3":        {"region": "North America / EU", "country_hint": "US / EU",          "confidence": 0.50},
    "Kraken 4":        {"region": "North America / EU", "country_hint": "US / EU",          "confidence": 0.50},
    "Bitstamp":        {"region": "Europe",             "country_hint": "European Union",   "confidence": 0.60},
    "Bitstamp 2":      {"region": "Europe",             "country_hint": "European Union",   "confidence": 0.60},
    # Asia — Korea
    "Upbit":           {"region": "Asia-Pacific",       "country_hint": "South Korea",      "confidence": 0.85},
    "Upbit 2":         {"region": "Asia-Pacific",       "country_hint": "South Korea",      "confidence": 0.85},
    "Bithumb":         {"region": "Asia-Pacific",       "country_hint": "South Korea",      "confidence": 0.85},
    # Asia — China / SE Asia
    "Huobi":           {"region": "Asia-Pacific",       "country_hint": "China / SE Asia",  "confidence": 0.60},
    "Huobi 2":         {"region": "Asia-Pacific",       "country_hint": "China / SE Asia",  "confidence": 0.60},
    "Huobi 3":         {"region": "Asia-Pacific",       "country_hint": "China / SE Asia",  "confidence": 0.60},
    "Huobi 4":         {"region": "Asia-Pacific",       "country_hint": "China / SE Asia",  "confidence": 0.60},
    "OKX":             {"region": "Asia-Pacific",       "country_hint": "China / SE Asia",  "confidence": 0.55},
    "OKX 2":           {"region": "Asia-Pacific",       "country_hint": "China / SE Asia",  "confidence": 0.55},
    "MEXC":            {"region": "Asia-Pacific",       "country_hint": "China / SE Asia",  "confidence": 0.55},
    "MEXC 2":          {"region": "Asia-Pacific",       "country_hint": "China / SE Asia",  "confidence": 0.55},
    "Gate.io":         {"region": "Asia-Pacific",       "country_hint": "China / SE Asia",  "confidence": 0.50},
    "Gate.io 2":       {"region": "Asia-Pacific",       "country_hint": "China / SE Asia",  "confidence": 0.50},
    "KuCoin":          {"region": "Asia-Pacific",       "country_hint": "SE Asia",          "confidence": 0.45},
    "KuCoin 2":        {"region": "Asia-Pacific",       "country_hint": "SE Asia",          "confidence": 0.45},
    "KuCoin 3":        {"region": "Asia-Pacific",       "country_hint": "SE Asia",          "confidence": 0.45},
    "Crypto.com":      {"region": "Asia-Pacific",       "country_hint": "SE Asia",          "confidence": 0.40},
    "Crypto.com 2":    {"region": "Asia-Pacific",       "country_hint": "SE Asia",          "confidence": 0.40},
    "Crypto.com 3":    {"region": "Asia-Pacific",       "country_hint": "SE Asia",          "confidence": 0.40},
    # Global / broad
    "Binance Hot Wallet":   {"region": "Global",        "country_hint": "Global",           "confidence": 0.25},
    "Binance Hot Wallet 2": {"region": "Global",        "country_hint": "Global",           "confidence": 0.25},
    "Binance Hot Wallet 3": {"region": "Global",        "country_hint": "Global",           "confidence": 0.25},
    "Binance Hot Wallet 4": {"region": "Global",        "country_hint": "Global",           "confidence": 0.25},
    "Binance Hot Wallet 5": {"region": "Global",        "country_hint": "Global",           "confidence": 0.25},
    "Binance Hot Wallet 6": {"region": "Global",        "country_hint": "Global",           "confidence": 0.25},
    "Binance Hot Wallet 7": {"region": "Global",        "country_hint": "Global",           "confidence": 0.25},
    "Binance Cold Wallet":  {"region": "Global",        "country_hint": "Global",           "confidence": 0.25},
    "Binance BUSD Pool":    {"region": "Global",        "country_hint": "Global",           "confidence": 0.25},
    "Binance BSC Hot Wallet": {"region": "Global",      "country_hint": "Global",           "confidence": 0.25},
    "Binance Solana Wallet":  {"region": "Global",      "country_hint": "Global",           "confidence": 0.25},
    "Bybit":           {"region": "Global",             "country_hint": "Global",           "confidence": 0.30},
    "Bybit 2":         {"region": "Global",             "country_hint": "Global",           "confidence": 0.30},
    "Bitfinex":        {"region": "Global",             "country_hint": "Global",           "confidence": 0.25},
    "Bitfinex 2":      {"region": "Global",             "country_hint": "Global",           "confidence": 0.25},
    "Bitfinex 3":      {"region": "Global",             "country_hint": "Global",           "confidence": 0.25},
}

# ---------------------------------------------------------------------------
# Blue-chip NFT collections on Ethereum (contract address → collection name)
# ---------------------------------------------------------------------------
_BLUE_CHIP_NFTS: dict[str, str] = {
    "0xbc4ca0eda7647a8ab7c2061c2e118a18a936f13d": "BAYC",
    "0xb47e3cd837ddf8e4c57f05d70ab865de6e193bbb": "CryptoPunks",
    "0x60e4d786628fea6478f785a6d7e704777c86a7c6": "MAYC",
    "0x49cf6f5d44e70224e2e23fdcdd2c053f30ada28b": "CloneX",
    "0x8a90cab2b38dba80c64b7734e58ee1db38b8992e": "Doodles",
    "0x23581767a106ae21c074b2276d25e5c3e136a68b": "Moonbirds",
    "0xa3aee8bce55beea1951ef834b99f3ac60d1abeeb": "VeeFriends",
    "0x1a92f7381b9f03921564a437210bb9396471050c": "Cool Cats",
    "0x9c8ff814952a187441e4dc10a67d38d3ca635dd4": "Nouns",
    "0x34d85c9cdeb23fa97cb08333b511ac86e1c4e258": "Otherdeed",
}


def _to_checksum(address: str) -> str:
    try:
        from web3 import Web3
        return Web3.to_checksum_address(address)
    except Exception:
        return address


def resolve_ens_name(w3, address: str) -> str | None:
    """Resolve ENS reverse record with 1-hour cache. Returns e.g. 'vitalik.eth' or None."""
    key = address.lower()
    now = time.monotonic()

    # Cache hit
    if key in _ENS_CACHE:
        name, ts = _ENS_CACHE[key]
        if now - ts < _ENS_CACHE_TTL:
            return name

    try:
        name = w3.ens.name(address)
    except Exception as e:
        logger.debug(f"ENS resolution failed for {address}: {e}")
        name = None

    _ENS_CACHE[key] = (name, now)
    return name


def get_wallet_funding_source(rpc_url: str, address: str) -> dict:
    """
    Finds the first inbound ETH transfer (wallet's original funder) using Alchemy's
    alchemy_getAssetTransfers API. Silently returns {} on any failure (non-Alchemy providers).

    Returns: {funder_address, first_activity_date, wallet_age_days}
    """
    try:
        checksum = _to_checksum(address)
        payload = {
            "jsonrpc": "2.0",
            "method": "alchemy_getAssetTransfers",
            "params": [{
                "toAddress": checksum,
                "category": ["external"],
                "maxCount": "0x1",
                "order": "asc",
                "withMetadata": True,
            }],
            "id": 1,
        }
        resp = requests.post(rpc_url, json=payload, timeout=15)
        resp.raise_for_status()
        data = resp.json()

        if "error" in data:
            return {}

        transfers = data.get("result", {}).get("transfers", [])
        if not transfers:
            return {}

        first = transfers[0]
        from_addr = first.get("from", "")
        block_time = first.get("metadata", {}).get("blockTimestamp")

        result: dict = {}
        if from_addr:
            result["funder_address"] = from_addr.lower()
        if block_time:
            dt = datetime.fromisoformat(block_time.replace("Z", "+00:00"))
            now = datetime.now(timezone.utc)
            result["first_activity_date"] = dt.strftime("%Y-%m-%d")
            result["wallet_age_days"] = (now - dt).days

        return result

    except Exception as e:
        logger.debug(f"alchemy_getAssetTransfers failed for {address}: {e}")
        return {}


def get_nft_summary(rpc_url: str, address: str) -> dict:
    """
    Gets NFT holdings count and blue-chip collection detection using Alchemy's alchemy_getNFTs.
    Silently returns empty result on any failure.

    Returns: {nft_count, has_nfts, has_blue_chip_nfts, blue_chip_collections}
    """
    try:
        checksum = _to_checksum(address)
        payload = {
            "jsonrpc": "2.0",
            "method": "alchemy_getNFTs",
            "params": [{"owner": checksum, "omitMetadata": True}],
            "id": 1,
        }
        resp = requests.post(rpc_url, json=payload, timeout=15)
        resp.raise_for_status()
        data = resp.json()

        if "error" in data:
            return _empty_nft()

        result_data = data.get("result", {})
        total_count = result_data.get("totalCount", 0)
        owned_nfts = result_data.get("ownedNfts", [])

        blue_chips: set[str] = set()
        for nft in owned_nfts:
            contract = nft.get("contract", {}).get("address", "").lower()
            if contract in _BLUE_CHIP_NFTS:
                blue_chips.add(_BLUE_CHIP_NFTS[contract])

        return {
            "nft_count": int(total_count) if total_count else 0,
            "has_nfts": bool(total_count and int(total_count) > 0),
            "has_blue_chip_nfts": bool(blue_chips),
            "blue_chip_collections": sorted(blue_chips),
        }

    except Exception as e:
        logger.debug(f"alchemy_getNFTs failed for {address}: {e}")
        return _empty_nft()


def _empty_nft() -> dict:
    return {"nft_count": 0, "has_nfts": False, "has_blue_chip_nfts": False, "blue_chip_collections": []}


def get_country_signal_from_cex(cex_label_name: str) -> dict:
    """Return country/region signal dict for a CEX label name, or {}."""
    return CEX_COUNTRY_SIGNALS.get(cex_label_name, {})


def enrich_wallet_identity(
    address: str,
    chain: str,
    rpc_url: str | None,
    w3=None,
    wallet_type: str = "USER",
    est_net_worth_usd: float = 0.0,
    tx_count: int = 0,
) -> dict:
    """
    Main identity enrichment entry point. Runs best-effort enrichment for USER wallets:
      - ENS name (Ethereum only, 1-hour cache)
      - Wallet age + first funding source (Alchemy API)
      - Country/region signal (derived from funding source CEX)
      - NFT holdings summary (Ethereum + Alchemy API)

    ENS, funding source, and NFT calls run IN PARALLEL (ThreadPoolExecutor, max 3 workers)
    to cut wall-clock time from ~3× latency to ~1× latency.

    Small wallets (< $50 AND < 5 tx) are skipped entirely — they are very unlikely
    to have ENS names, NFTs, or meaningful funding sources.

    Returns a flat dict to be merged into activity_indicators.
    Non-USER/UNKNOWN wallet types return {} immediately (no overhead).
    """
    if wallet_type not in ("USER", "UNKNOWN"):
        return {}

    is_evm = chain != "solana"
    if not is_evm or not rpc_url:
        return {}

    # Skip enrichment for clearly small wallets — saves 3 API calls per wallet
    if est_net_worth_usd < 50 and tx_count < 5:
        return {}

    is_eth = chain == "ethereum"

    # Submit all I/O-bound calls in parallel
    with ThreadPoolExecutor(max_workers=3) as executor:
        f_ens     = executor.submit(resolve_ens_name, w3, address)     if is_eth and w3 else None
        f_funding = executor.submit(get_wallet_funding_source, rpc_url, address)
        f_nft     = executor.submit(get_nft_summary, rpc_url, address) if is_eth else None

        ens_name = f_ens.result()     if f_ens     else None
        funding  = f_funding.result()
        nft_data = f_nft.result()     if f_nft     else {}

    result: dict = {}

    # ENS
    if ens_name:
        result["ens_name"] = ens_name

    # Wallet age + funder address
    if funding:
        result.update(funding)

        # Country signal: match funder against known CEX labels
        funder_addr = funding.get("funder_address")
        if funder_addr:
            from .chains import get_known_label
            funder_label = get_known_label(chain, funder_addr)
            if funder_label and funder_label.get("type") == "exchange":
                cex_name = funder_label.get("name", "")
                country_info = get_country_signal_from_cex(cex_name)
                if country_info:
                    result["funding_source"] = cex_name
                    result["region"] = country_info.get("region", "Unknown")
                    result["country_hint"] = country_info.get("country_hint", "Global")
                    result["country_confidence"] = country_info.get("confidence", 0.3)

    # NFT summary
    if nft_data:
        result.update(nft_data)

    return result
