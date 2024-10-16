import gzip

import json

from governenv.constants import DATA_DIR

# open DATA_DIR / "sentiment.jsonl.gz"

# load the data
with gzip.open(DATA_DIR / "sentiment.jsonl.gz", "rt") as f:
    sentiment = [json.loads(line) for line in f]
