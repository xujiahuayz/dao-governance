"""Script to process votes data."""

from collections import defaultdict
import glob
import json


from tqdm import tqdm

import pandas as pd
from governenv.constants import DATA_DIR, PROCESSED_DATA_DIR

# load the vote data for all proposals
votes_files = glob.glob(str(DATA_DIR / "snapshot" / "votes" / "*.jsonl"))
df_votes = []
for file in tqdm(votes_files):
    proposal_id = file.split("/")[-1].replace(".jsonl", "")
    with open(
        file,
        "r",
        encoding="utf-8",
    ) as f:
        df_vote = defaultdict(list)
        for line in f:
            vote = json.loads(line)
            for col in [
                "id",
                "ipfs",
                "voter",
                "created",
                "metadata",
                "reason",
                "app",
                "vp",
                "vp_by_strategy",
                "vp_state",
            ]:
                df_vote[col].append(vote[col])
            if isinstance(vote["choice"], dict):
                df_vote["type"].append("dict")
                df_vote["choice"].append(vote["choice"])
            elif isinstance(vote["choice"], list):
                df_vote["type"].append("list")
                df_vote["choice"].append(vote["choice"])
            elif isinstance(vote["choice"], str):
                df_vote["type"].append("string")
                df_vote["choice"].append(vote["choice"])
            else:
                df_vote["type"].append("single")
                df_vote["choice"].append(int(vote["choice"]))
            df_vote["proposal_id"].append(vote["proposal"]["id"])
        if len(df_vote) == 0:
            continue

    df_vote = pd.DataFrame(df_vote)
    df_votes.append(df_vote)
df_votes = pd.concat(df_votes, ignore_index=True)
df_votes = df_votes.loc[df_votes["vp"] > 0]
df_votes.to_csv(PROCESSED_DATA_DIR / "votes.csv", index=False)
