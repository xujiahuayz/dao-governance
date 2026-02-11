"""Script to process protocols event time"""

import gzip
import json
import pandas as pd
from governenv.constants import (
    SNAPSHOT_PATH_PROPOSALS,
    PROCESSED_DATA_DIR,
    SNAPSHOT_PATH_NETWORKS,
)


proposals = []

# load the data
with gzip.open(SNAPSHOT_PATH_PROPOSALS, "rt") as f:
    # load data and skip duplicates
    for line in f:
        data = json.loads(line)
        proposal = {
            "id": data["id"],
            "title": data["title"],
            "body": data["body"],
            "space": data["space"]["id"],
            "type": data["type"],
            "strategies": data["strategies"],
            "validation": data["validation"],
            "quorum": data["quorum"],
            "quorum_type": data["quorumType"],
            "discussion": data["discussion"],
            "choices": data["choices"],
            "state": data["state"],
            "scores": data["scores"],
            "scores_by_strategy": data["scores_by_strategy"],
            "created": data["created"],
            "start": data["start"],
            "end": data["end"],
            "votes": data["votes"],
            "network": data["network"],
        }
        proposals.append(proposal)

proposals = pd.DataFrame(proposals)

# keep only closed proposals
proposals = proposals.loc[proposals["state"] == "closed"]

# Translate the network id to network name
proposals["network"] = proposals["network"].astype(str)
with gzip.open(
    SNAPSHOT_PATH_NETWORKS,
    "rt",
    encoding="utf-8",
) as f:
    networks = {json.loads(line)["id"]: json.loads(line)["name"] for line in f}

# Network 42 has no mapping in the snapshot networks, replace it with polygon
proposals["network"] = proposals["network"].replace({"42": "137"})
proposals["network_name"] = proposals["network"].apply(networks.get)

proposals.to_csv(PROCESSED_DATA_DIR / "proposals_spaces.csv", index=False)
