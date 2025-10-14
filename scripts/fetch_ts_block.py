"""Script to fetch block timestamps from DeFiLlama"""

import os
import pandas as pd
from tqdm import tqdm

from scripts.process_event_study import df_proposals_adj
from governenv.defillama import DefiLlama
from governenv.constants import PROCESSED_DATA_DIR


defillama = DefiLlama()

if os.path.exists(PROCESSED_DATA_DIR / "proposals_adjusted_with_block.csv"):
    df_proposals_adj_block_exists = pd.read_csv(
        PROCESSED_DATA_DIR / "proposals_adjusted_with_block.csv"
    )
    finished_ids = set(df_proposals_adj_block_exists["id"].tolist())
    unfinished = df_proposals_adj[~df_proposals_adj["id"].isin(finished_ids)]
    df_proposals_adj = unfinished

df_proposals_adj_block = []

for _, row in tqdm(df_proposals_adj.iterrows(), total=len(df_proposals_adj)):
    for col in ["start", "end", "created"]:
        for col in [f"{col}_ts_-5d", f"{col}_ts_+5d", f"{col}_ts"]:
            row[f"{col}_block"] = defillama.get_block_by_timestamp(row[col])
    df_proposals_adj_block.append(row)

if os.path.exists(PROCESSED_DATA_DIR / "proposals_adjusted_with_block.csv"):
    df_proposals_adj_block = pd.concat(
        [df_proposals_adj_block_exists, pd.DataFrame(df_proposals_adj_block)],
        ignore_index=True,
    )
else:
    df_proposals_adj_block = pd.DataFrame(df_proposals_adj_block)
df_proposals_adj_block.to_csv(
    f"{PROCESSED_DATA_DIR}/proposals_adjusted_with_block.csv", index=False
)
