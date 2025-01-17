"""
Calculate the total number of votes; the number of voters when it reached 50% of the total voting power for each proposal; and the timestamp when it reached 50% of the total voting power for each proposal.
"""

from governenv.constants import DATA_DIR
import json
import gzip
from collections import Counter, OrderedDict

# Filter proposals from the compressed JSONL file
with gzip.open(DATA_DIR / "snapshot_proposals.jsonl.gz", "r") as f:
    filtered_data = [
        {
            "id": w["id"],
            "link": w["link"],
            "discussion": w["discussion"],
        }
        for line in f
        if (w := json.loads(line)).get("space", {}).get("id") == "ens.eth"
    ]

filtered_proposals = {entry["id"]: entry for entry in filtered_data}


# For each proposal, count total number of votes and calculate VP sums
with open(DATA_DIR / "snapshot_votes.jsonl", "r") as file1:
    data1 = [json.loads(line) for line in file1]

filtered_results = {
    entry["id"]: {
        "vp_sum": 0,
        **entry,
        "number": 0,
        "half_vp_sum_time": None,
        "break_count": None,
    }
    for entry in filtered_data
}

# Count occurrences and the sum of all voting power for each proposal
for entry in data1:
    proposal_id = entry["proposal"]["id"]
    if proposal_id in filtered_proposals:
        filtered_results[proposal_id]["vp_sum"] += entry["vp"]
        filtered_results[proposal_id]["number"] += 1


# Count time when it reaches 50% of vp_sum for each proposal
for proposal_id, result in filtered_results.items():
    vp_sum = result["vp_sum"]
    half_vp_sum = vp_sum / 2
    vp_sum_time = 0
    for entry in data1:
        if entry["proposal"]["id"] == proposal_id:
            vp_sum_time += entry["vp"]
            if vp_sum_time >= half_vp_sum:
                result["half_vp_sum_time"] = entry["created"]
                break


# Calculate the number of votes required to reach 50% of vp_sum for each proposal
for proposal_id, result in filtered_results.items():
    vp_sum = result["vp_sum"]
    half_vp_sum = vp_sum / 2
    vp_sum_voter = 0

    # Extract and sort all "vp" values for this proposal in descending order
    proposal_vps = sorted(
        [entry["vp"] for entry in data1 if entry["proposal"]["id"] == proposal_id],
        reverse=True,
    )

    # Calculate the break count when it reaches 50% of vp_sum
    break_count = 0
    for vp in proposal_vps:
        vp_sum_voter += vp
        break_count += 1
        if vp_sum_voter >= half_vp_sum:
            result["break_count"] = break_count
            break

# Calculate ratio of number to half_voters_count
for proposal_id, result in filtered_results.items():
    if result["number"] is None or result["break_count"] is None:
        result["ratio"] = None
    else:
        result["ratio"] = result["break_count"] / result["number"]


output_data = [
    OrderedDict(
        [
            ("id", result["id"]),
            ("link", result["link"]),
            ("discussion", result["discussion"]),
            ("number", result["number"]),
            ("vp_sum", result["vp_sum"]),
            ("half_vp_sum_time", result["half_vp_sum_time"]),
            ("half_voters_count", result["break_count"]),
            ("ratio", result["ratio"]),
        ]
    )
    for result in filtered_results.values()
]

output_file_path = DATA_DIR / "ens_vp.json"
with open(output_file_path, "w") as output_file:
    json.dump(output_data, output_file, indent=4)
