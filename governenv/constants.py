from governenv.settings import PROJECT_ROOT

DATA_DIR = PROJECT_ROOT / "data"
SNAPSHOT_PATH = DATA_DIR / "snapshot.jsonl.gz"
SNAPSHOT_PATH_PROPOSALS = DATA_DIR / "snapshot_proposals.jsonl.gz"
SNAPSHOT_PATH_VOTES = DATA_DIR / "snapshot_votes.jsonl.gz"
GITHUB_PATH_IP_PULLREQUESTS = DATA_DIR / "IPs_pullRequests.jsonl.gz"
GITHUB_PATH_REFCLIENT_ISSUES = DATA_DIR / "RefClient_issues.jsonl.gz"
GITHUB_PATH_REFCLIENT_PULLREQUESTS = DATA_DIR / "RefClient_pullRequests.jsonl.gz"