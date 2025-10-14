"""Constants."""

from governenv.settings import (
    PROJECT_ROOT,
    SNAPSHOT_API_KEY,
    INFURA_API_KEY,
)

# Directories and File Paths
DATA_DIR = PROJECT_ROOT / "data"
ABI_DIR = PROJECT_ROOT / "abi"
PROCESSED_DATA_DIR = PROJECT_ROOT / "processed_data"
FIGURE_DIR = PROJECT_ROOT / "figures"
SNAPSHOT_PATH = DATA_DIR / "snapshot.jsonl.gz"
SNAPSHOT_PATH_PROPOSALS = DATA_DIR / "snapshot_proposals.jsonl.gz"
SNAPSHOT_PATH_VOTES = DATA_DIR / "snapshot_votes.jsonl.gz"
SNAPSHOT_PATH_STATEMENTS = DATA_DIR / "snapshot_statements.jsonl.gz"
SNAPSHOT_PATH_DELEGATE = DATA_DIR / "snapshot_delegate.jsonl.gz"
SNAPSHOT_PATH_NETWORKS = DATA_DIR / "snapshot_networks.jsonl.gz"
GITHUB_PATH_IP_PULLREQUESTS = DATA_DIR / "IPs_pullRequests.jsonl.gz"
GITHUB_PATH_REFCLIENT_ISSUES = DATA_DIR / "refClient_issues.jsonl.gz"
GITHUB_PATH_REFCLIENT_PULLREQUESTS = DATA_DIR / "refClient_pullRequests.jsonl.gz"
KAIKO_PRICE_PATH = DATA_DIR / "kaiko_price.json.gz"
BITCOIN_NODES_GEO_PATH = DATA_DIR / "bitnodes_country_data.jsonl.gz"
IMPROVEMENT_PROPOSALS_DIR = DATA_DIR / "ImprovementProposals"
REFERENCE_CLIENTS_DIR = DATA_DIR / "ReferenceClients"

# Transfer Data Update
CURRENT_BLOCK = 23514780
DUST_THRESHOLD = 1
WHALE_THRESHOLD = 0.1

# API Endpoints
SNAPSHOT_ENDPOINT = f"https://hub.snapshot.org/graphql?apiKey={SNAPSHOT_API_KEY}"
GRAPH_SNAPSHOT_ENDPOINT = "https://gateway.thegraph.com/api/subgraphs/id/\
4YgtogVaqoM8CErHWDK8mKQ825BcVdKB8vBYmb4avAQo"
INFURA_API_BASE = "https://mainnet.infura.io/v3/"
INFURA_ENDPOINT = f"{INFURA_API_BASE}{INFURA_API_KEY}"

# Snapshot Contract Address
SNAPSHOT_DELEGATION_ADDRESS = "0x469788fE6E9E9681C6ebF3bF78e7Fd26Fc015446"
SNAPSHOT_DELEGATION_START_BLOCK = 11225329

# Event Study Parameters
EST_LOWER = -250
EST_UPPER = -20
EVENT_WINDOW = 5

# HTTP Request Headers
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36"
    )
}

# Voting Characteristics
NO = {
    "no",
    "against",
    "nah",
    "keep",
    "deny",
    "reject",
    "leave",
    "disagree",
    "disapprove",
    "don't",
    "nay",
    "decline",
    "oppose",
    "nae",
    "maintain",
    "不同意",
}
YES = {
    "yes",
    "for",
    "looks good",
    "approve",
    "in favor",
    "agree",
    "accept",
    "pass",
    "yay",
    "support",
    "cool",
    "yae",
    "confirm",
    "同意",
}
ABSTAIN = {"abstain"}

# Exclusion Keywords
EXKW = [
    # remove social media
    "discord",
    "t.me",
    "t.co",
    "telegram",
    "x.com",
    "twitter",
    "reddit",
    "youtube",
    "youtu",
    "github",
    "bilibili",
    "gmail",
    # remove plain websites
    "baidu",
    "google",
    "coingecko",
    "blockscape",
    "helpen",
    "metamask.io",
    "opensea.io",
]
