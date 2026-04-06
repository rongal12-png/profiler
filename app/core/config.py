import os
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from pydantic_settings import BaseSettings
from functools import lru_cache

# Load environment variables from .env file at the project root
load_dotenv()

class Settings(BaseSettings):
    # Database
    DATABASE_URL: str = os.getenv("DATABASE_URL", "postgresql://user:password@postgres/wallet_intel")

    # Celery
    CELERY_BROKER_URL: str = os.getenv("CELERY_BROKER_URL", "redis://redis:6379/0")
    CELERY_RESULT_BACKEND: str = os.getenv("CELERY_RESULT_BACKEND", "redis://redis:6379/0")

    # RPC URLs
    ETHEREUM_RPC_URL: str | None = os.getenv("ETHEREUM_RPC_URL")
    BASE_RPC_URL: str | None = os.getenv("BASE_RPC_URL")
    ARBITRUM_RPC_URL: str | None = os.getenv("ARBITRUM_RPC_URL")
    OPTIMISM_RPC_URL: str | None = os.getenv("OPTIMISM_RPC_URL")
    POLYGON_RPC_URL: str | None = os.getenv("POLYGON_RPC_URL")
    AVALANCHE_RPC_URL: str | None = os.getenv("AVALANCHE_RPC_URL")
    FANTOM_RPC_URL: str | None = os.getenv("FANTOM_RPC_URL")
    BSC_RPC_URL: str | None = os.getenv("BSC_RPC_URL")
    SOLANA_RPC_URL: str | None = os.getenv("SOLANA_RPC_URL")
    HEDERA_RPC_URL: str | None = os.getenv("HEDERA_RPC_URL", "https://mainnet.hashio.io/api")
    TON_RPC_URL: str | None = os.getenv("TON_RPC_URL", "https://toncenter.com/api/v2")

    # External APIs
    COINGECKO_API_KEY: str | None = os.getenv("COINGECKO_API_KEY")

    # Tiering Logic (Configurable)
    WHALE_LIQUID_THRESHOLD: int = 1_000_000
    WHALE_STABLE_THRESHOLD: int = 250_000
    TUNA_LIQUID_THRESHOLD: int = 100_000
    TUNA_STABLE_THRESHOLD: int = 25_000

    # Admin API
    ADMIN_API_KEY: str = os.getenv("ADMIN_API_KEY", "")
    SANCTIONS_CACHE_DIR: str = os.getenv("SANCTIONS_CACHE_DIR", "/tmp/sanctions_cache")

    # Analysis constants
    ERC20_ABI_MINIMAL: list = [
        {"constant": True, "inputs": [{"name": "_owner", "type": "address"}], "name": "balanceOf", "outputs": [{"name": "balance", "type": "uint256"}], "type": "function"},
        {"constant": True, "inputs": [], "name": "decimals", "outputs": [{"name": "", "type": "uint8"}], "type": "function"},
        {"constant": True, "inputs": [], "name": "symbol", "outputs": [{"name": "", "type": "string"}], "type": "function"}
    ]
    SOL_MINT_ADDRESS: str = "So11111111111111111111111111111111111111112"


@lru_cache()
def get_settings():
    return Settings()

settings = get_settings()

# Database setup
engine = create_engine(
    settings.DATABASE_URL,
    pool_size=20,
    max_overflow=30,
    pool_timeout=10,
    pool_pre_ping=True,
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
