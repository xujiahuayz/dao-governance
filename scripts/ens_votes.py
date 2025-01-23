"""
Calculate the total number of votes; the number of voters when it reached 50% of the total voting power for each proposal; and the timestamp when it reached 50% of the total voting power for each proposal.
"""

import gzip
import json
from governenv.constants import DATA_DIR
from datetime import datetime

with gzip.open(DATA_DIR / "snapshot_proposals.jsonl.gz", "r") as f:
    filtered_results = [
        {
            "id": proposal["id"],
            "link": proposal.get("link", ""),
            "discussion": proposal.get("discussion", ""),
            "number": 0,
            "vp_sum": 0,
            "half_vp_sum_time": None,
            "UTC_time": None,
            "half_voters_count": None,
            "ratio": None,
        }
        for line in f
        if (proposal := json.loads(line)).get("space", {}).get("id") == "ens.eth"
    ]

with gzip.open(DATA_DIR / "snapshot_votes.jsonl.gz", "r") as f:
    votes = [json.loads(line) for line in f]

for result in filtered_results:
    proposal_id = result["id"]

    # Filter votes related to the current proposal
    filtered_votes = [
        entry for entry in votes if entry["proposal"]["id"] == proposal_id
    ]

    # Calculate total voting power and the number of votes for the current proposal
    vp_sum = sum(entry["vp"] for entry in filtered_votes)
    result["vp_sum"] = vp_sum
    result["number"] = len(filtered_votes)

    # Calculate the time when voting power reaches 50%
    half_vp_sum = vp_sum / 2
    cumulative_vp = 0
    for entry in filtered_votes:
        cumulative_vp += entry["vp"]
        if cumulative_vp >= half_vp_sum:
            result["half_vp_sum_time"] = entry["created"]
            result["UTC_time"] = datetime.utcfromtimestamp(entry["created"]).isoformat()
            break

    # Calculate the break count (number of voters needed to reach 50% of voting power)
    sorted_vps = sorted((entry["vp"] for entry in filtered_votes), reverse=True)
    cumulative_voter_vp = 0
    break_count = 0
    for vp in sorted_vps:
        cumulative_voter_vp += vp
        break_count += 1
        if cumulative_voter_vp >= half_vp_sum:
            result["half_voters_count"] = break_count
            break

    # Calculate the ratio of half_voters_count to total number of votes
    if result["number"] > 0 and result["half_voters_count"] is not None:
        result["ratio"] = result["half_voters_count"] / result["number"]

with open(DATA_DIR / "ens_vp.json", "w") as output_file:
    json.dump(filtered_results, output_file, indent=4)
