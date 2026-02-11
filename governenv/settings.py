"""Settings and configuration."""

import os
from pathlib import Path

try:
    # Optional: only if you keep a .env file locally
    from dotenv import load_dotenv  # pip install python-dotenv

    load_dotenv()
except Exception:
    pass

# Base Project Directory
PROJECT_ROOT = Path(__file__).parent.parent

# Data Paths
DATA_DIR = Path(os.environ.get("DATA_DIR", PROJECT_ROOT)) / "data"
PROCESSED_DATA_DIR = (
    Path(os.environ.get("PROCESSED_DATA_DIR", PROJECT_ROOT)) / "processed_data"
)
os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(PROCESSED_DATA_DIR, exist_ok=True)

# API Keys and Secrets
HEADERS = os.environ.get("HEADERS")
KAIKO_API_KEY = os.environ.get("KAIKO_API_KEY")
TALLY_API_KEY = os.environ.get("TALLY_API_KEY")
SNAPSHOT_API_KEY = os.environ.get("SNAPSHOT_API_KEY")
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN")
COINGECKO_API_KEY = os.environ.get("COINGECKO_API_KEY")
DEFILLAMA_API_KEY = os.environ.get("DEFILLAMA_API_KEY")
THEGRAPH_API_KEY = os.environ.get("THEGRAPH_API_KEY")
ALCHEMY_API_KEY = os.environ.get("ALCHEMY_API_KEY")
ETHERSCAN_API_KEY = os.environ.get("ETHERSCAN_API_KEY")
INFURA_API_KEYS = os.environ.get("INFURA_API_KEYS", "").split(",")
INFURA_API_KEY = INFURA_API_KEYS[0]
INFURA_API_KEYS = INFURA_API_KEYS[1:]
