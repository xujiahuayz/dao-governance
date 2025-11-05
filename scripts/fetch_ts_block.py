"""Script to fetch block timestamps from DeFiLlama"""

import os
import json
import pandas as pd
from tqdm import tqdm

from governenv.defillama import DefiLlama
from governenv.constants import PROCESSED_DATA_DIR

SAVE_PATH = PROCESSED_DATA_DIR / "snapshot_block.json"

defillama = DefiLlama()

df_proposals_with_sc = pd.read_csv(PROCESSED_DATA_DIR / "proposals_with_sc.csv")


all_tasks = []
for _, row in df_proposals_with_sc.iterrows():

    # fetch block numbers for start, end, created and their +/- 5 day timestamps
    for col in ["start", "end", "created"]:
        for col_name in [f"{col}_ts_-5d", f"{col}_ts_+5d"]:
            all_tasks.append(row[col_name])

    # fetch created block for voting power calculation
    all_tasks.append(row["created_ts"])

all_tasks = set(all_tasks)

if os.path.exists(SAVE_PATH):
    with open(SAVE_PATH, "r", encoding="utf-8") as f:
        snapshot_block = json.load(f)
    fetched_ts = set(int(ts) for ts in snapshot_block.keys())
    all_tasks = all_tasks - fetched_ts
else:
    snapshot_block = {}

# Fetch block numbers for all unique timestamps
for ts in tqdm(all_tasks):
    try:
        snapshot_block[ts] = defillama.get_block_by_timestamp(ts)
    except Exception as e:
        print(f"Failed to fetch block for timestamp {ts}: {e}")

# Save the results
with open(SAVE_PATH, "w", encoding="utf-8") as f:
    json.dump(snapshot_block, f, indent=4)
