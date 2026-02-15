import requests
import time
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

# RPC retry configuration
MAX_RETRIES = 3
RETRY_DELAY = 1.0  # seconds
RETRY_BACKOFF = 2.0  # exponential backoff multiplier

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
                    if attempt < max_retries - 1:
                        logger.warning(
                            f"RPC call {func.__name__} failed (attempt {attempt + 1}/{max_retries}): {e}. "
                            f"Retrying in {current_delay:.1f}s..."
                        )
                        time.sleep(current_delay)
                        current_delay *= backoff
                    else:
                        logger.error(
                            f"RPC call {func.__name__} failed after {max_retries} attempts: {e}"
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
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        data = response.json()
        return {key: value.get('usd', 0) for key, value in data.items()}
    except requests.RequestException as e:
        logger.error(f"Could not fetch prices from CoinGecko: {e}")
        return {key: 0 for key in coingecko_ids}


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
