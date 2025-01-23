"""
Calculate the total number of votes; the number of voters when it reached 50% of the total voting power for each proposal; and the timestamp when it reached 50% of the total voting power for each proposal.
"""

import gzip
import json
from datetime import UTC, datetime

from governenv.constants import DATA_DIR

with gzip.open(DATA_DIR / "snapshot_votes.jsonl.gz", "r") as f:
    votes = [json.loads(line) for line in f]

filtered_results = []

with gzip.open(DATA_DIR / "snapshot_proposals.jsonl.gz", "r") as f:
    for line in f:
        proposal = json.loads(line)
        space_id = proposal["space"]["id"]
        if space_id == "ens.eth":
            proposal_id = proposal["id"]

            # Filter votes related to the current proposal
            filtered_votes = [
                entry for entry in votes if entry["proposal"]["id"] == proposal_id
            ]

            # Calculate total voting power and the number of votes for the current proposal
            vp_sum = sum(entry["vp"] for entry in filtered_votes)
            number_votes = len(filtered_votes)

            # Calculate the time when voting power reaches 50%
            half_vp_sum = vp_sum / 2
            cumulative_vp = 0

            for entry in filtered_votes:
                cumulative_vp += entry["vp"]
                if cumulative_vp >= half_vp_sum:
                    half_vp_sum_time = entry["created"]
                    UTC_time = datetime.fromtimestamp(entry["created"], UTC).isoformat()
                    break

            # Calculate the break count (number of voters needed to reach 50% of voting power)
            sorted_vps = sorted((entry["vp"] for entry in filtered_votes), reverse=True)
            cumulative_voter_vp = 0
            break_count = 0
            for vp in sorted_vps:
                cumulative_voter_vp += vp
                break_count += 1
                if cumulative_voter_vp >= half_vp_sum:
                    half_voters_count = break_count
                    break

            # Calculate the ratio of half_voters_count to total number of votes
            ratio = (
                (half_voters_count / number_votes)
                if number_votes > 0 and half_voters_count is not None
                else None
            )

            filtered_results.append(
                {
                    "id": proposal_id,
                    "link": proposal["link"],
                    "discussion": proposal["discussion"],
                    "number": number_votes,
                    "vp_sum": vp_sum,
                    "half_voters_count": half_voters_count,
                    "ratio": ratio,
                    "half_vp_sum_time": half_vp_sum_time,
                    "UTC_time": UTC_time,
                }
            )


with open(DATA_DIR / "ens_vp.json", "w") as output_file:
    json.dump(filtered_results, output_file, indent=4)
