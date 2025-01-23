"""
Calculate the total number of votes; the number of voters when it reached 50% of the total voting power for each proposal; and the timestamp when it reached 50% of the total voting power for each proposal.
"""

import gzip
import json

from governenv.constants import DATA_DIR

# Filter proposals from the compressed JSONL file
with gzip.open(DATA_DIR / "snapshot_proposals.jsonl.gz", "r") as f:
    filtered_results = [
        w
        for line in f
        if (w := json.loads(line)).get("space", {}).get("id") == "ens.eth"
    ]

with gzip.open(DATA_DIR / "snapshot_votes.jsonl.gz", "r") as f:
    votes = [json.loads(line) for line in f]

for result in filtered_results:

    proposal_id = result["id"]
    filtered_votes = [entry for entry in votes if entry["proposal"] == proposal_id]

    vp_sum = sum(entry["vp"] for entry in filtered_votes)

    result["vp_sum"] = vp_sum
    result["number"] = len(filtered_votes)

    # Count time when it reaches 50% of vp_sum for each proposal
    half_vp_sum = vp_sum / 2
    vp_sum_time = 0
    for entry in filtered_votes:
        vp_sum_time += entry["vp"]
        if vp_sum_time >= half_vp_sum:
            result["half_vp_sum_time"] = entry["created"]
            break

    # Extract and sort all "vp" values for this proposal in descending order
    proposal_vps = sorted(
        [entry["vp"] for entry in filtered_votes],
        reverse=True,
    )

    # Calculate the break count when it reaches 50% of vp_sum
    break_count = 0
    vp_sum_voter = 0
    for vp in proposal_vps:
        vp_sum_voter += vp
        break_count += 1
        if vp_sum_voter >= half_vp_sum:
            result["break_count"] = break_count
            break

    # Calculate ratio of number to half_voters_count
    if result["number"] == 0 or result["break_count"] is None:
        result["ratio"] = None
    else:
        result["ratio"] = result["break_count"] / result["number"]


with open(DATA_DIR / "ens_vp.json", "w") as output_file:
    json.dump(filtered_results, output_file, indent=4)
