"""Script to fetch discussion."""

import re
import json
import os
import time

import pandas as pd
import numpy as np
import requests
from tqdm import tqdm

from governenv.constants import DATA_DIR, PROCESSED_DATA_DIR, SHUT_DOWN, SPECIAL


os.makedirs(DATA_DIR / "discussion", exist_ok=True)


def check_forum_link(link: str) -> bool:
    """Check if the link is a forum link."""

    return len(parts := link.split("/")) > 3 and parts[3] == "t"


def can_int(x) -> bool:
    """Check if x can be converted to int."""
    try:
        int(x)
        return True
    except (ValueError, TypeError):
        return False


# Load proposals data
df_proposals = pd.read_csv(PROCESSED_DATA_DIR / "proposals_with_sc_blocks.csv")
df_proposals = df_proposals[["id", "space", "body", "discussion"]]

# Split proposals with and without discussion links
df_proposals_w_discussion = df_proposals.loc[~df_proposals["discussion"].isna()].copy()
df_proposals_wo_discussion = df_proposals.loc[df_proposals["discussion"].isna()].copy()

# Extract discussion links from body for proposals without discussion links
df_proposals_wo_discussion["discussion"] = df_proposals_wo_discussion["body"].apply(
    lambda x: (re.findall(r"https?://[^\s)\]>]+(?<![.,])", str(x)))
)
df_proposals_wo_discussion["discussion"] = df_proposals_wo_discussion[
    "discussion"
].apply(lambda x: list(set([_ for _ in x if check_forum_link(_)])))
df_proposals_wo_discussion = df_proposals_wo_discussion.loc[
    df_proposals_wo_discussion["discussion"].apply(lambda x: len(x) == 1)
]
df_proposals_wo_discussion["discussion"] = df_proposals_wo_discussion[
    "discussion"
].apply(lambda x: x[0])

# Keep only forum links in proposals with discussion links
df_proposals_w_discussion = df_proposals_w_discussion.loc[
    df_proposals_w_discussion["discussion"].apply(check_forum_link)
]

# Combine proposals with and without discussion links
df_proposals = pd.concat(
    [df_proposals_w_discussion, df_proposals_wo_discussion], ignore_index=True
)
df_proposals["discussion_id"] = df_proposals["discussion"].apply(
    lambda x: (
        x.split("/")[5]
        if len(x.split("/")) >= 6 and can_int(x.split("/")[5])
        else np.nan
    )
)
df_proposals["discussion_root"] = df_proposals["discussion"].apply(
    lambda x: x.split("/")[2]
)

for url, discussion_id in SPECIAL.items():
    df_proposals.loc[df_proposals["discussion"] == url, "discussion_id"] = discussion_id

df_proposals = df_proposals.loc[
    (~df_proposals["discussion_id"].isna()) & (~df_proposals["space"].isin(SHUT_DOWN))
].copy()

df_proposals.to_csv(PROCESSED_DATA_DIR / "proposals_discussion.csv", index=False)

# Fetch balancer forum discussion
for space in df_proposals["space"].unique():
    os.makedirs(DATA_DIR / "discussion" / space, exist_ok=True)

    if space in SHUT_DOWN:
        print(f"Skipping {space} as the forum is shut down.")
        continue

    for idx, row in tqdm(
        df_proposals.loc[df_proposals["space"] == space].iterrows(),
        total=len(df_proposals.loc[df_proposals["space"] == space]),
        desc=f"Fetching discussions for {space}",
    ):
        header = row["discussion_root"]

        # Handle special cases
        if row["discussion"] in SPECIAL:
            discussion_id = SPECIAL[row["discussion"]]
        else:
            discussion_id = row["discussion"].split("/")[5]

        # Fetch discussion JSON
        file_path = DATA_DIR / "discussion" / space / f"{discussion_id}.json"
        if file_path.exists():
            continue
        time.sleep(5)

        URL = f"https://{header}/t/{discussion_id}.json?track_visit=true&forceLoad=true"
        try:
            res = requests.get(URL, timeout=10)
        except Exception as e:
            print(
                f"Error fetching discussion {discussion_id} for proposal {row['id']}: {e}"
            )
            continue

        if res.status_code != 200:
            print(
                f"Failed to fetch discussion {discussion_id} for proposal {row['id']}"
            )
            continue
        res = res.json()

        # Check if discussion exists
        if "post_stream" not in res:
            print(f"Discussion {discussion_id} not found, skipping.")
            continue

        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(res, f, ensure_ascii=False, indent=4)
