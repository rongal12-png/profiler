import re as _re_module
import requests
import time
from urllib.parse import urlparse, urlunparse
from web3 import Web3
from web3.exceptions import Web3Exception
from solders.pubkey import Pubkey
from solana.rpc.api import Client
from solana.exceptions import SolanaRpcException
from functools import lru_cache, wraps
from .config import settings, get_settings
from .chains import get_chain_config
import logging

logger = logging.getLogger(__name__)

# Simple in-memory cache with TTL
_price_cache = {}
CACHE_TTL_SECONDS = 300 # 5 minutes

# Token metadata cache (rarely changes, long TTL)
_token_metadata_cache: dict[str, dict | None] = {}
_token_metadata_cache_time: dict[str, float] = {}
TOKEN_METADATA_TTL = 86400  # 24 hours

# RPC retry configuration
MAX_RETRIES = 3
RETRY_DELAY = 1.0  # seconds
RETRY_BACKOFF = 2.0  # exponential backoff multiplier

# Multicall3 — deployed at the same address on all major EVM chains
MULTICALL3_ADDRESS = "0xcA11bde05977b3631167028862bE2a173976CA11"
MULTICALL3_ABI = [
    {
        "inputs": [
            {
                "components": [
                    {"internalType": "address", "name": "target", "type": "address"},
                    {"internalType": "bool", "name": "allowFailure", "type": "bool"},
                    {"internalType": "bytes", "name": "callData", "type": "bytes"},
                ],
                "internalType": "struct Multicall3.Call3[]",
                "name": "calls",
                "type": "tuple[]",
            }
        ],
        "name": "aggregate3",
        "outputs": [
            {
                "components": [
                    {"internalType": "bool", "name": "success", "type": "bool"},
                    {"internalType": "bytes", "name": "returnData", "type": "bytes"},
                ],
                "internalType": "struct Multicall3.Result[]",
                "name": "returnData",
                "type": "tuple[]",
            }
        ],
        "stateMutability": "payable",
        "type": "function",
    }
]

# ERC20 function selectors
_ERC20_BALANCEOF_SIG = bytes.fromhex("70a08231")  # keccak256("balanceOf(address)")[:4]
_ERC20_DECIMALS_SIG = bytes.fromhex("313ce567")   # keccak256("decimals()")[:4]


def _sanitize_error(error: Exception) -> str:
    """C4: Sanitize error messages to avoid leaking RPC URLs with API keys."""
    msg = str(error)
    # Replace URLs containing API keys (common patterns: /v2/KEY, ?apikey=KEY, /KEY/)
    msg = _re_module.sub(r'https?://[^\s"\'<>]+', '[RPC_URL]', msg)
    return msg


# --- Retry Decorator ---
def retry_on_rpc_error(max_retries=MAX_RETRIES, delay=RETRY_DELAY, backoff=RETRY_BACKOFF):
    """Decorator to retry RPC calls with exponential backoff on failure."""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None
            current_delay = delay

            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except (Web3Exception, SolanaRpcException, requests.RequestException, TimeoutError) as e:
                    last_exception = e
                    safe_msg = _sanitize_error(e)
                    if attempt < max_retries - 1:
                        logger.warning(
                            f"RPC call {func.__name__} failed (attempt {attempt + 1}/{max_retries}): {safe_msg}. "
                            f"Retrying in {current_delay:.1f}s..."
                        )
                        time.sleep(current_delay)
                        current_delay *= backoff
                    else:
                        logger.error(
                            f"RPC call {func.__name__} failed after {max_retries} attempts: {safe_msg}"
                        )

            # If all retries failed, raise the last exception
            if last_exception:
                raise last_exception

        return wrapper
    return decorator

# --- Caching Decorator ---
def timed_lru_cache(seconds: int, maxsize: int = 128):
    def wrapper_cache(func):
        func = lru_cache(maxsize=maxsize)(func)
        func.ttl = seconds
        func.expiration = time.monotonic() + seconds

        @wraps(func)
        def wrapped_func(*args, **kwargs):
            if time.monotonic() >= func.expiration:
                func.cache_clear()
                func.expiration = time.monotonic() + seconds
            return func(*args, **kwargs)
        return wrapped_func
    return wrapper_cache


# --- Price Fetching ---
@timed_lru_cache(seconds=CACHE_TTL_SECONDS)
def get_token_prices(coingecko_ids: tuple[str]) -> dict[str, float]:
    """Fetches token prices from CoinGecko."""
    logger.info(f"Fetching prices for: {coingecko_ids}")
    ids_str = ",".join(coingecko_ids)
    url = f"https://api.coingecko.com/api/v3/simple/price?ids={ids_str}&vs_currencies=usd"

    headers = {}
    if settings.COINGECKO_API_KEY:
        url = f"https://pro-api.coingecko.com/api/v3/simple/price?ids={ids_str}&vs_currencies=usd&x_cg_pro_api_key={settings.COINGECKO_API_KEY}"

    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        data = response.json()
        return {key: value.get('usd', 0) for key, value in data.items()}
    except requests.RequestException as e:
        logger.error(f"Could not fetch prices from CoinGecko: {e}")
        return {key: 0 for key in coingecko_ids}


# DeFiLlama chain name mapping (their coin format)
_DEFILLAMA_CHAIN_MAP = {
    "ethereum": "ethereum",
    "base": "base",
    "arbitrum": "arbitrum",
    "polygon": "polygon",
    "optimism": "optimism",
    "bsc": "bsc",
    "avalanche": "avax",
    "fantom": "fantom",
    "solana": "solana",
}


# Per-token DeFiLlama price cache: {"chain:0xaddress": (price_float, timestamp)}
# Keyed per individual token so all wallets sharing the same token hit the cache.
_llama_price_cache: dict[str, tuple[float, float]] = {}


def get_token_prices_by_address(chain: str, contract_addresses: tuple) -> dict:
    """
    Fetches token USD prices by contract address using DeFiLlama Coins API (free, no key).
    Returns {contract_address_lower: usd_price}.

    Uses a per-token cache (TTL = CACHE_TTL_SECONDS = 5 min) so that wallets sharing
    tokens (e.g. both holding WETH) don't repeat the same fetch.
    Only uncached tokens are sent to DeFiLlama in a single batched request.
    """
    if not contract_addresses:
        return {}

    now = time.monotonic()
    llama_chain = _DEFILLAMA_CHAIN_MAP.get(chain, chain)
    result: dict[str, float] = {}
    to_fetch: list[str] = []

    for addr in contract_addresses:
        key = f"{llama_chain}:{addr.lower()}"
        if key in _llama_price_cache:
            price, ts = _llama_price_cache[key]
            if now - ts < CACHE_TTL_SECONDS:
                result[addr.lower()] = price
                continue
        to_fetch.append(addr.lower())

    if not to_fetch:
        return result  # 100% cache hit

    url = f"https://coins.llama.fi/prices/current/{','.join(f'{llama_chain}:{a}' for a in to_fetch)}"
    try:
        resp = requests.get(url, timeout=15)
        resp.raise_for_status()
        coins = resp.json().get("coins", {})
        for coin_id, info in coins.items():
            addr = coin_id.split(":")[-1].lower()
            price = float(info.get("price", 0))
            result[addr] = price
            _llama_price_cache[f"{llama_chain}:{addr}"] = (price, now)
        logger.info(f"DeFiLlama: fetched {len(coins)}/{len(to_fetch)} new prices on {chain} "
                    f"({len(contract_addresses) - len(to_fetch)} from cache)")
    except Exception as e:
        logger.warning(f"DeFiLlama price lookup failed for {chain}: {_sanitize_error(e)}")

    return result


# --- Alchemy Token API ---
@retry_on_rpc_error()
def get_all_evm_token_balances(rpc_url: str, address: str) -> list[dict]:
    """
    Uses Alchemy's alchemy_getTokenBalances to discover ALL ERC-20 tokens
    held by an address in a single API call.
    Returns list of {contract_address, balance_hex}.
    """
    try:
        checksum = Web3.to_checksum_address(address)
        payload = {
            "jsonrpc": "2.0",
            "method": "alchemy_getTokenBalances",
            "params": [checksum, "erc20"],
            "id": 1,
        }
        resp = requests.post(rpc_url, json=payload, timeout=30)
        resp.raise_for_status()
        data = resp.json()

        if "error" in data:
            logger.warning(f"Alchemy token balances error for {address}: {data['error']}")
            return []

        token_balances = data.get("result", {}).get("tokenBalances", [])

        # Filter out zero balances
        non_zero = []
        for tb in token_balances:
            hex_bal = tb.get("tokenBalance", "0x0")
            if hex_bal and hex_bal != "0x" and hex_bal != "0x0" and int(hex_bal, 16) > 0:
                non_zero.append({
                    "contract_address": tb["contractAddress"],
                    "balance_raw": int(hex_bal, 16),
                })

        logger.info(f"Found {len(non_zero)} tokens for {address}")
        return non_zero

    except Exception as e:
        logger.error(f"Failed to get all token balances for {address}: {e}")
        return []


@retry_on_rpc_error()
def get_token_metadata(rpc_url: str, contract_address: str) -> dict | None:
    """
    Uses Alchemy's alchemy_getTokenMetadata to get token name, symbol, decimals.
    Results are cached for 24 hours since token metadata rarely changes.
    """
    cache_key = contract_address.lower()
    now = time.monotonic()

    # Check cache
    if cache_key in _token_metadata_cache:
        if now - _token_metadata_cache_time.get(cache_key, 0) < TOKEN_METADATA_TTL:
            return _token_metadata_cache[cache_key]

    try:
        payload = {
            "jsonrpc": "2.0",
            "method": "alchemy_getTokenMetadata",
            "params": [contract_address],
            "id": 1,
        }
        resp = requests.post(rpc_url, json=payload, timeout=15)
        resp.raise_for_status()
        data = resp.json()

        if "error" in data:
            return None

        result = data.get("result", {})
        metadata = {
            "symbol": result.get("symbol", "???"),
            "name": result.get("name", "Unknown"),
            "decimals": result.get("decimals", 18),
        }

        # Cache the result
        _token_metadata_cache[cache_key] = metadata
        _token_metadata_cache_time[cache_key] = now

        return metadata
    except Exception as e:
        logger.debug(f"Failed to get metadata for {contract_address}: {e}")
        return None


def discover_evm_tokens(rpc_url: str, address: str, max_tokens: int = 30) -> list[dict]:
    """
    Discovers all ERC-20 tokens held by an address using Alchemy API.
    Returns list of {symbol, name, contract_address, amount, balance_raw, decimals}.
    Fetches metadata in parallel for speed.
    """
    from concurrent.futures import ThreadPoolExecutor

    raw_balances = get_all_evm_token_balances(rpc_url, address)
    if not raw_balances:
        return []

    # Sort by balance (descending) and limit to top N
    raw_balances.sort(key=lambda x: x["balance_raw"], reverse=True)
    raw_balances = raw_balances[:max_tokens]

    # Fetch metadata in parallel
    results = []

    def fetch_one(tb):
        meta = get_token_metadata(rpc_url, tb["contract_address"])
        if meta and meta["symbol"] != "???" and meta["decimals"] is not None:
            decimals = meta["decimals"]
            amount = tb["balance_raw"] / (10 ** decimals) if decimals > 0 else tb["balance_raw"]
            if amount > 0:
                return {
                    "symbol": meta["symbol"],
                    "name": meta["name"],
                    "contract_address": tb["contract_address"],
                    "amount": amount,
                    "decimals": decimals,
                }
        return None

    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = [executor.submit(fetch_one, tb) for tb in raw_balances]
        for f in futures:
            result = f.result()
            if result:
                results.append(result)

    return results


# --- EVM Batch & Multicall3 ---

@retry_on_rpc_error()
def batch_evm_core_calls(rpc_url: str, address: str) -> tuple[float, bool, int]:
    """
    Fetches native balance, code (is_contract flag), and tx count in a SINGLE HTTP request
    using JSON-RPC batch. Reduces 3 round-trips to 1.
    Returns (native_balance_eth, is_contract, tx_count).
    """
    checksum = Web3.to_checksum_address(address)
    batch = [
        {"jsonrpc": "2.0", "id": 1, "method": "eth_getBalance",          "params": [checksum, "latest"]},
        {"jsonrpc": "2.0", "id": 2, "method": "eth_getCode",             "params": [checksum, "latest"]},
        {"jsonrpc": "2.0", "id": 3, "method": "eth_getTransactionCount", "params": [checksum, "latest"]},
    ]
    resp = requests.post(rpc_url, json=batch, timeout=30)
    resp.raise_for_status()
    data = resp.json()

    # Some providers return a single error object instead of an array when batch is unsupported
    if isinstance(data, dict):
        raise Web3Exception(f"JSON-RPC batch not supported by provider: {data.get('error', data)}")

    by_id = {r["id"]: r.get("result") for r in data}
    balance_wei = int(by_id[1], 16)
    code = by_id[2]
    tx_count = int(by_id[3], 16)
    return (
        balance_wei / 1e18,
        bool(code and code != "0x" and len(code) > 2),
        tx_count,
    )


def multicall3_erc20_balances(w3: Web3, address: str, token_configs: dict[str, str]) -> list[dict]:
    """
    Fetches ERC20 balanceOf + decimals for multiple tokens in a SINGLE eth_call via Multicall3.
    Reduces N×2 RPC calls to 1. Falls back silently to empty list on failure.
    token_configs: {symbol: token_address}
    Returns: [{symbol, address, amount}] for tokens with non-zero balance.
    """
    if not token_configs:
        return []

    try:
        checksum_wallet = Web3.to_checksum_address(address)
        # ABI-encode the wallet address as a 32-byte padded value for balanceOf(address)
        padded_wallet = b'\x00' * 12 + bytes.fromhex(checksum_wallet[2:])

        token_list = list(token_configs.items())  # [(symbol, addr), ...]
        calls = []
        for _, token_addr in token_list:
            checksum_token = Web3.to_checksum_address(token_addr)
            calls.append((checksum_token, True, _ERC20_BALANCEOF_SIG + padded_wallet))
            calls.append((checksum_token, True, _ERC20_DECIMALS_SIG))

        multicall = w3.eth.contract(
            address=Web3.to_checksum_address(MULTICALL3_ADDRESS),
            abi=MULTICALL3_ABI,
        )
        results = multicall.functions.aggregate3(calls).call()

        balances = []
        for i, (symbol, token_addr) in enumerate(token_list):
            success_bal, data_bal = results[i * 2]
            success_dec, data_dec = results[i * 2 + 1]
            if success_bal and success_dec and len(data_bal) >= 32 and len(data_dec) >= 32:
                balance_raw = int.from_bytes(data_bal[:32], "big")
                decimals = int.from_bytes(data_dec[:32], "big")
                if balance_raw > 0 and decimals <= 30:
                    balances.append({
                        "symbol": symbol,
                        "address": token_addr,
                        "amount": balance_raw / (10 ** decimals),
                    })
        return balances

    except Exception as e:
        logger.warning(f"Multicall3 ERC20 balances failed for {address}: {_sanitize_error(e)}")
        return []


# --- EVM Chain Interaction ---
@lru_cache(maxsize=10)
def get_w3_instance(chain: str) -> Web3:
    """Gets a cached Web3 instance for a given EVM chain with timeout configuration."""
    config = get_chain_config(chain)
    # Configure HTTP provider with timeout (30 seconds for requests)
    provider = Web3.HTTPProvider(
        config['rpc_url'],
        request_kwargs={'timeout': 30}
    )
    return Web3(provider)

@retry_on_rpc_error()
def get_evm_native_balance(w3: Web3, address: str) -> float:
    """Gets the native token balance for an EVM address."""
    try:
        checksum_address = Web3.to_checksum_address(address)
        balance_wei = w3.eth.get_balance(checksum_address)
        return w3.from_wei(balance_wei, 'ether')
    except Exception as e:
        logger.error(f"Failed to get EVM native balance for {address}: {e}")
        return 0.0

@retry_on_rpc_error()
def get_evm_token_balance(w3: Web3, address: str, token_address: str) -> float:
    """Gets an ERC20 token balance for an EVM address."""
    try:
        checksum_address = Web3.to_checksum_address(address)
        checksum_token_address = Web3.to_checksum_address(token_address)
        contract = w3.eth.contract(address=checksum_token_address, abi=settings.ERC20_ABI_MINIMAL)
        balance_raw = contract.functions.balanceOf(checksum_address).call()
        decimals = contract.functions.decimals().call()
        return balance_raw / (10 ** decimals)
    except Exception as e:
        # Handle cases where the contract call fails (e.g., not a valid ERC20)
        logger.debug(f"Failed to get ERC20 balance for {address} token {token_address}: {e}")
        return 0.0

@retry_on_rpc_error()
def is_evm_contract(w3: Web3, address: str) -> bool:
    """Checks if an EVM address is a smart contract."""
    try:
        checksum_address = Web3.to_checksum_address(address)
        code = w3.eth.get_code(checksum_address)
        return code != b''
    except Exception as e:
        logger.error(f"Failed to check if {address} is contract: {e}")
        return False

@retry_on_rpc_error()
def get_evm_tx_count(w3: Web3, address: str) -> int:
    """Gets the transaction count (nonce) for an EVM address."""
    try:
        checksum_address = Web3.to_checksum_address(address)
        return w3.eth.get_transaction_count(checksum_address)
    except Exception as e:
        logger.error(f"Failed to get transaction count for {address}: {e}")
        return 0


# --- Solana Chain Interaction ---
@lru_cache(maxsize=3)
def get_solana_client(chain: str) -> Client:
    """Gets a cached Solana client instance."""
    config = get_chain_config(chain)
    return Client(config['rpc_url'])

@retry_on_rpc_error()
def get_sol_native_balance(client: Client, address: str) -> float:
    """Gets the native SOL balance."""
    try:
        pubkey = Pubkey.from_string(address)
        balance_lamports = client.get_balance(pubkey).value
        return balance_lamports / 1e9 # 1 SOL = 10^9 Lamports
    except (ValueError, SolanaRpcException) as e:
        logger.error(f"Failed to get SOL balance for {address}: {e}")
        return 0.0

@retry_on_rpc_error()
def get_sol_token_balance(client: Client, address: str, mint_address: str) -> float:
    """Gets a SPL token balance."""
    try:
        owner_pubkey = Pubkey.from_string(address)
        mint_pubkey = Pubkey.from_string(mint_address)

        # Find the associated token account
        response = client.get_token_accounts_by_owner(owner_pubkey, mint=mint_pubkey)
        if not response.value:
            return 0.0

        # Assume the first account is the primary one
        account_address = response.value[0].pubkey
        balance_response = client.get_token_account_balance(account_address)
        return float(balance_response.value.ui_amount_string)
    except (ValueError, SolanaRpcException) as e:
        logger.debug(f"Failed to get SPL token balance for {address} token {mint_address}: {e}")
        return 0.0

@retry_on_rpc_error()
def is_solana_contract(client: Client, address: str) -> bool:
    """Checks if a Solana address is an executable program."""
    try:
        pubkey = Pubkey.from_string(address)
        account_info = client.get_account_info(pubkey).value
        return account_info.executable if account_info else False
    except (ValueError, SolanaRpcException) as e:
        logger.error(f"Failed to check if {address} is Solana contract: {e}")
        return False

@retry_on_rpc_error()
def get_sol_tx_count(client: Client, address: str) -> int:
    """Gets the transaction count for a Solana address."""
    try:
        pubkey = Pubkey.from_string(address)
        # Limit to 1000 signatures for performance, this is an indicator not an exact count
        signatures = client.get_signatures_for_address(pubkey, limit=1000).value
        return len(signatures)
    except (ValueError, SolanaRpcException) as e:
        logger.error(f"Failed to get transaction count for {address}: {e}")
        return 0
