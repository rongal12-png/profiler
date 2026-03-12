import json
from pathlib import Path
from .config import settings

# Load known labels from JSON file
_LABELS_FILE = Path(__file__).parent.parent / "data" / "known_labels.json"
_labels_data = []
if _LABELS_FILE.exists():
    with open(_LABELS_FILE) as f:
        _labels_data = json.load(f).get("labels", [])

# Build lookup index: {chain: {address_lower: {type, name, confidence, source}}}
KNOWN_LABELS: dict[str, dict[str, dict]] = {}
for _entry in _labels_data:
    _chain = _entry["chain"]
    _addr = _entry["address"]
    if _chain != "solana":
        _addr = _addr.lower()
    KNOWN_LABELS.setdefault(_chain, {})[_addr] = {
        "type": _entry["label_type"],
        "name": _entry["label_name"],
        "wallet_type": _entry.get("wallet_type", "UNKNOWN"),
        "confidence": _entry.get("confidence", 0.9),
        "source": _entry.get("source", "unknown"),
    }

# Mapping from label_type to wallet_type for heuristic fallback
LABEL_TYPE_TO_WALLET_TYPE = {
    "exchange": "CEX_EXCHANGE",
    "dex_router": "DEX_ROUTER",
    "bridge": "BRIDGE",
    "protocol": "PROTOCOL",
    "burn": "PROTOCOL",
    "vc": "USER",
    "kol": "USER",
    "smart_money": "USER",
}

CHAIN_CONFIG = {
    "ethereum": {
        "id": 1,
        "rpc_url": settings.ETHEREUM_RPC_URL,
        "native_symbol": "ETH",
        "coingecko_id": "ethereum",
        "stables": {
            "USDC": "0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48",
            "USDT": "0xdAC17F958D2ee523a2206206994597C13D831ec7",
            "DAI": "0x6B175474E89094C44Da98b954EedeAC495271d0F",
        },
        "top_tokens": {
            "WETH": "0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2",
            "WBTC": "0x2260FAC5E5542a773Aa44fBCfeDf7C193bc2C599",
        },
        "staked_tokens": {
            "stETH": "0xae7ab96520DE3A18E5e111B5EaAb095312D7fE84",
            "rETH": "0xae78736Cd615f374D3085123A210448E74Fc6393",
            "cbETH": "0xBe9895146f7AF43049ca1c1AE358B0541Ea49704",
        },
        "governance_tokens": {
            "UNI": "0x1f9840a85d5aF5bf1D1762F925BDADdC4201F984",
            "AAVE": "0x7Fc66500c84A76Ad7e9c93437bFc5Ac33E2DDaE9",
            "LDO": "0x5A98FcBEA516Cf06857215779Fd812CA3beF1B32",
            "MKR": "0x9f8F72aA9304c8B593d555F12eF6589cC3A579A2",
        },
    },
    "base": {
        "id": 8453,
        "rpc_url": settings.BASE_RPC_URL,
        "native_symbol": "ETH",
        "coingecko_id": "ethereum",
        "stables": {
            "USDC": "0x833589fCD6eDb6E08f4c7C32D4f71b54bda02913",
        },
        "top_tokens": {
            "WETH": "0x4200000000000000000000000000000000000006",
        },
        "staked_tokens": {
            "cbETH": "0x2Ae3F1Ec7F1F5012CFEab0185bfc7aa3cf0DEc22",
        },
        "governance_tokens": {},
    },
    "arbitrum": {
        "id": 42161,
        "rpc_url": settings.ARBITRUM_RPC_URL,
        "native_symbol": "ETH",
        "coingecko_id": "ethereum",
        "stables": {
            "USDC": "0xaf88d065e77c8cC2239327C5EDb3A432268e5831",
            "USDT": "0xFd086bC7CD5C481DCC9C85ebE478A1C0b69FCbb9",
        },
        "top_tokens": {
            "WETH": "0x82aF49447D8a07e3bd95BD0d56f35241523fBab1",
        },
        "staked_tokens": {
            "wstETH": "0x5979D7b546E38E9aB8E6549DB3B1B1F30deA4f79",
        },
        "governance_tokens": {
            "ARB": "0x912CE59144191C1204E64559FE8253a0e49E6548",
        },
    },
    "polygon": {
        "id": 137,
        "rpc_url": settings.POLYGON_RPC_URL,
        "native_symbol": "MATIC",
        "coingecko_id": "matic-network",
        "stables": {
            "USDC": "0x2791Bca1f2de4661ED88A30C99A7a9449Aa84174",
            "USDT": "0xc2132D05D31c914a87C6611C10748AEb04B58e8F",
        },
        "top_tokens": {
            "WETH": "0x7ceb23fd6bc0add59e62ac25578270cff1b9f619",
            "WMATIC": "0x0d500B1d8E8eF31E21C99d1Db9A6444d3ADf1270",
        },
        "staked_tokens": {
            "stMATIC": "0x3A58a54C066FdC0f2D55FC9C89F0415C92eBf3C4",
        },
        "governance_tokens": {
            "AAVE": "0xD6DF932A45C0f255f85145f286eA0b292B21C90B",
        },
    },
    "optimism": {
        "id": 10,
        "rpc_url": settings.OPTIMISM_RPC_URL,
        "native_symbol": "ETH",
        "coingecko_id": "ethereum",
        "stables": {
            "USDC": "0x7F5c764cBc14f9669B88837ca1490cCa17c31607",
            "USDT": "0x94b008aA00579c1307B0EF2c499aD98a8ce58e58",
            "DAI":  "0xDA10009cBd5D07dd0CeCc66161FC93D7c9000da1",
        },
        "top_tokens": {
            "WETH": "0x4200000000000000000000000000000000000006",
            "OP":   "0x4200000000000000000000000000000000000042",
        },
        "staked_tokens": {
            "wstETH": "0x1F32b1c2345538c0c6f582fCB022739c4A194Ebb",
        },
        "governance_tokens": {
            "OP": "0x4200000000000000000000000000000000000042",
        },
    },
    "bsc": {
        "id": 56,
        "rpc_url": settings.BSC_RPC_URL,
        "native_symbol": "BNB",
        "coingecko_id": "binancecoin",
        "stables": {
            "BUSD": "0xe9e7CEA3DedcA5984780Bafc599bD69ADd087D56",
            "USDT": "0x55d398326f99059fF775485246999027B3197955",
            "USDC": "0x8AC76a51cc950d9822D68b83fE1Ad97B32Cd580d",
        },
        "top_tokens": {
            "WBNB": "0xbb4CdB9CBd36B01bD1cBaEBF2De08d9173bc095c",
            "CAKE": "0x0E09FaBB73Bd3Ade0a17ECC321fD13a19e81cE82",
        },
        "staked_tokens": {},
        "governance_tokens": {
            "CAKE": "0x0E09FaBB73Bd3Ade0a17ECC321fD13a19e81cE82",
        },
    },
    "avalanche": {
        "id": 43114,
        "rpc_url": settings.AVALANCHE_RPC_URL,
        "native_symbol": "AVAX",
        "coingecko_id": "avalanche-2",
        "stables": {
            "USDC":   "0xB97EF9Ef8734C71904D8002F8b6Bc66Dd9c48a6E",
            "USDC.e": "0xA7D7079b0FEaD91F3e65f86E8915Cb59c1a4C664",
            "USDT.e": "0xc7198437980c041c805A1EDcbA50c1Ce5db95118",
        },
        "top_tokens": {
            "WAVAX": "0xB31f66AA3C1e785363F0875A1B74E27b85FD66c7",
            "JOE":   "0x6e84a6216eA6dACC71eE8E6b0a5B7322EEbC0fDd",
        },
        "staked_tokens": {
            "sAVAX": "0x2b2C81e08f1Af8835a78Bb2A90AE924ACE0eA4bE",
        },
        "governance_tokens": {},
    },
    "fantom": {
        "id": 250,
        "rpc_url": settings.FANTOM_RPC_URL,
        "native_symbol": "FTM",
        "coingecko_id": "fantom",
        "stables": {
            "USDC":  "0x04068DA6C83AFCFA0e13ba15A6696662335D5B75",
            "fUSDT": "0x049d68029688eAbF473097a2fC38ef61633A3C7A",
        },
        "top_tokens": {
            "WFTM": "0x21be370D5312f44cB42ce377BC9b8a0cEF1A4C83",
        },
        "staked_tokens": {},
        "governance_tokens": {},
    },
    "solana": {
        "id": "solana",
        "rpc_url": settings.SOLANA_RPC_URL,
        "native_symbol": "SOL",
        "coingecko_id": "solana",
        "stables": {
            "USDC": "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v",
            "USDT": "Es9vMFrzaCERmJfrF4H2FYD4KCoNkY11McCe8BenwNYB",
        },
        "top_tokens": {},
        "staked_tokens": {
            "mSOL": "mSoLzYCxHdYgdzU16g5QSh3i5K3z3KZK7ytfqcJm7So",
            "JitoSOL": "J1toso1uCk3RLmjorhTtrVwY9HJ7X8V9yYac6Y7kGCPn",
        },
        "governance_tokens": {
            "JTO": "jtojtomepa8beP8AuQc6eXt5FriJwfFMwQx2v2f9mCL",
        },
    },
}


def get_chain_config(chain_name: str):
    config = CHAIN_CONFIG.get(chain_name.lower())
    if not config:
        raise ValueError(f"Unsupported chain: {chain_name}")
    if not config.get("rpc_url"):
        raise ValueError(f"RPC URL not configured for chain: {chain_name}")
    return config


def get_known_label(chain: str, address: str) -> dict | None:
    """Gets a known label for an address. Returns {type, name, confidence, source} or None."""
    lookup_addr = address if chain == "solana" else address.lower()
    return KNOWN_LABELS.get(chain, {}).get(lookup_addr)


def get_label_types_for_address(chain: str, address: str) -> list[str]:
    """Returns a list of label_type values for this address (e.g. ['vc', 'exchange'])."""
    label = get_known_label(chain, address)
    if label:
        return [label["type"]]
    return []


def get_wallet_type(chain: str, address: str, is_contract: bool = False) -> str:
    """
    Determines wallet_type using layered detection:
    A) Label list (highest confidence)
    B) Heuristic from label_type mapping
    C) Contract bytecode fallback
    """
    label = get_known_label(chain, address)
    if label:
        # Direct wallet_type from label data (highest confidence)
        return label.get("wallet_type", LABEL_TYPE_TO_WALLET_TYPE.get(label["type"], "UNKNOWN"))

    # Fallback: if it has bytecode but no label, it's a generic contract
    if is_contract:
        return "CONTRACT"

    return "USER"


# Backward compat alias
def get_public_label(chain: str, address: str) -> dict | None:
    return get_known_label(chain, address)
