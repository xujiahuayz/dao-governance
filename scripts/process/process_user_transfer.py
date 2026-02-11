"""Script to process DAO"""

import os
import json
import glob
from tqdm import tqdm

import pandas as pd
import numpy as np
from governenv.constant import DATA_PATH, PROCESSED_DATA_PATH

INPUT_GLOB = f"{DATA_PATH}/dao/sc_transfer/*.csv"
OUTPUT_DIR = f"{DATA_PATH}/dao/sc_transfer_by_space"
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Load space-contract mapping
with open(f"{DATA_PATH}/space_contract.json", "r") as f:
    sc = json.load(f)

space = set(sc.keys())

all_files = []
for token_file in tqdm(glob.glob(INPUT_GLOB)):
    df = pd.read_csv(token_file)
    all_files.append(df)

all_data = pd.concat(all_files, ignore_index=True)
all_data = all_data[
    [
        "tx_hash",
        "block_timestamp",
        "from_label",
        "to_label",
        "from_address",
        "to_address",
        "amount",
        "amount_usd",
    ]
]

for s in tqdm(space):
    mask = (all_data["from_label"] == s) | (all_data["to_label"] == s)
    df_space = all_data[mask].copy()
    df_space.to_csv(f"{OUTPUT_DIR}/{s}.csv", index=False)

df_proposal = pd.read_csv(PROCESSED_DATA_PATH / "proposal_voter_label.csv")
df_user = {
    "id": [],
    "space": [],
    "voter_user": [],
    "whale_user": [],
    "non_whale_user": [],
}
for space, group in tqdm(df_proposal.groupby("space")):

    if space not in sc:
        continue

    df = pd.read_csv(f"{OUTPUT_DIR}/{space}.csv")
    df["block_timestamp"] = pd.to_datetime(df["block_timestamp"])

    for proposal_id, df_prop in group.groupby("id"):

        created = df_prop["created"].iloc[0]
        df_subset = df[(df["block_timestamp"] <= created)].copy()
        user = set(df_subset["from_address"].unique()) | set(
            df_subset["to_address"].unique()
        )

        voters = set(df_prop["voter"].unique())
        whale = set(df_prop[df_prop["label"] == "whales"]["voter"].unique())
        non_whale = set(df_prop[df_prop["label"] != "whales"]["voter"].unique())

        voters_user = {v for v in voters if v in user}
        whale_user = {v for v in whale if v in user}
        non_whale_user = {v for v in non_whale if v in user}

        df_user["id"].append(proposal_id)
        df_user["space"].append(space)
        df_user["voter_user"].append(
            len(voters_user) / len(voters) if len(voters) > 0 else np.nan
        )
        df_user["whale_user"].append(
            len(whale_user) / len(whale) if len(whale) > 0 else np.nan
        )
        df_user["non_whale_user"].append(
            len(non_whale_user) / len(non_whale) if len(non_whale) > 0 else np.nan
        )

df_user = pd.DataFrame(df_user)
df_user.to_csv(PROCESSED_DATA_PATH / "proposal_user.csv", index=False)
