from governenv.settings import PROJECT_ROOT, SNAPSHOT_API_KEY

DATA_DIR = PROJECT_ROOT / "data"
SNAPSHOT_PATH = DATA_DIR / "snapshot.jsonl.gz"
SNAPSHOT_PATH_PROPOSALS = DATA_DIR / "snapshot_proposals.jsonl.gz"
SNAPSHOT_PATH_VOTES = DATA_DIR / "snapshot_votes.jsonl.gz"
SNAPSHOT_PATH_STATEMENTS = DATA_DIR / "snapshot_statements.jsonl.gz"
SNAPSHOT_PATH_DELEGATE = DATA_DIR / "snapshot_delegate.jsonl.gz"
GITHUB_PATH_IP_PULLREQUESTS = DATA_DIR / "IPs_pullRequests.jsonl.gz"
GITHUB_PATH_REFCLIENT_ISSUES = DATA_DIR / "refClient_issues.jsonl.gz"
GITHUB_PATH_REFCLIENT_PULLREQUESTS = DATA_DIR / "refClient_pullRequests.jsonl.gz"
KAIKO_PRICE_PATH = DATA_DIR / "kaiko_price.json.gz"
BITCOIN_NODES_GEO_PATH = DATA_DIR / "bitnodes_country_data.jsonl.gz"
IMPROVEMENT_PROPOSALS_DIR = DATA_DIR / "ImprovementProposals"
REFERENCE_CLIENTS_DIR = DATA_DIR / "ReferenceClients"

SNAPSHOT_ENDPOINT = f"https://hub.snapshot.org/graphql?apiKey={SNAPSHOT_API_KEY}"
