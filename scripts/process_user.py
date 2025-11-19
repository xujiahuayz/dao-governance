"""Script to process protocol user"""

import re
import json
from ast import literal_eval
from collections import defaultdict

import pandas as pd
from tqdm import tqdm

from governenv.constants import DATA_DIR, PROCESSED_DATA_DIR


REMOVE = {
    "synthereum.eth": "uniswap",
    "pagedao.eth": "uniswap",
    "pickle.eth": "uniswap",
    "primexyz.eth": "balancer",
}

CHANGE = {"timelessfi.eth": "timeless", "freerossdao.eth": "freerossdao"}

df_proposals = pd.read_csv(PROCESSED_DATA_DIR / "proposals_with_sc_blocks.csv")
df_proposals["address"] = df_proposals["address"].apply(literal_eval)

space_address = defaultdict(set)

for _, row in df_proposals.iterrows():
    for addr in row["address"]:
        space_address[row["space"]].add(addr["address"].lower())


df_label = pd.read_csv(DATA_DIR / "label_flipside.csv")

# Create a mapping from space to set of labels
space_label_dict = defaultdict(set)
for space, addr_list in tqdm(space_address.items()):
    for addr in addr_list:
        label_row = df_label.loc[df_label["ADDRESS"] == addr]
        if not label_row.empty:
            if (space in REMOVE) and (label_row["LABEL"].values[0] == REMOVE[space]):
                continue
            if space in CHANGE:
                space_label_dict[space].add(CHANGE[space])
            else:
                space_label_dict[space].add(label_row["LABEL"].values[0])
        else:
            print(f"Address {space} {addr} not found in label file.")

with open(PROCESSED_DATA_DIR / "space_label.json", "w", encoding="utf-8") as fout:
    json.dump(
        {space: list(labels) for space, labels in space_label_dict.items()},
        fout,
        indent=4,
    )

space_contract = defaultdict(set)
for space, labels in tqdm(space_label_dict.items()):
    for label in labels:
        df_label_subset = df_label.loc[
            df_label["LABEL"].str.contains(
                rf"\b{re.escape(label)}\b", regex=True, case=False, na=False
            )
        ]
        for _, row in df_label_subset.iterrows():
            space_contract[space].add(row["ADDRESS"])

with open(PROCESSED_DATA_DIR / "space_contract.json", "w", encoding="utf-8") as fout:
    json.dump(
        {space: list(addresses) for space, addresses in space_contract.items()},
        fout,
        indent=4,
    )
