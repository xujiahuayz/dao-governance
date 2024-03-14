from governenv.settings import PROJECT_ROOT

DATA_DIR = PROJECT_ROOT / "data"
SNAPSHOT_PATH = DATA_DIR / "snapshot.jsonl.gz"
SNAPSHOT_PATH_PROPOSALS = DATA_DIR / "snapshot_proposals.jsonl.gz"
SNAPSHOT_PATH_VOTES = DATA_DIR / "snapshot_votes.jsonl.gz"
GITHUB_PATH_PULL_REQUESTS = DATA_DIR / "GitHub_pullRequests.jsonl.gz"