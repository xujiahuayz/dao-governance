"""
Filter ENS links (with discussion link) from snapshot:
"""

from governenv.constants import DATA_DIR
import json

with open(DATA_DIR / "snapshot_proposals.jsonl", "r") as f:
    data_unique = {
        w["id"]: w["discussion"] 
        for line in {json.dumps(row, sort_keys=True) for row in (json.loads(line) for line in f)}
        if (w := json.loads(line)).get("space", {}).get("id") == "ens.eth" and len(w.get("discussion", "")) > 5 
    }

with open(DATA_DIR / "ens_snapshot_filtered.json", "w") as f:
    json.dump(data_unique, f, indent=4)