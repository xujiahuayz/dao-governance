"""Merge spaces data with Coingecko list."""

import gzip
import json

import pandas as pd

from governenv.constants import SNAPSHOT_PATH, DATA_DIR, PROCESSED_DATA_DIR

# load the data
with gzip.open(SNAPSHOT_PATH, "rt") as f:
    # load data and skip duplicates
    spaces = [json.loads(line) for line in f]

# keep proposal number > 0, has coingecko id, and verified
spaces = [
    item
    for item in spaces
    if (item["proposalsCount"] > 0) & (item["coingecko"] is not None) & item["verified"]
]
df_spaces = pd.DataFrame(spaces).rename(
    columns={"id": "space_id", "name": "space_name"}
)[["space_id", "space_name", "coingecko", "validation", "network", "strategies"]]

# Load coingecko list
cg_list = pd.read_csv(DATA_DIR / "coingecko_coins.csv").rename(
    columns={"id": "coingecko"}
)[["coingecko", "symbol", "name"]]
df_spaces = cg_list.merge(df_spaces, on="coingecko", how="left").dropna(
    subset=["space_id"]
)

# manual check and corrections
incorrect_space_id = [
    "pinfts.eth",
]
df_spaces = df_spaces[~df_spaces["space_id"].isin(incorrect_space_id)]

# aggregate
df_spaces = (
    df_spaces.groupby("coingecko")
    .agg(
        {
            "space_id": list,
            "space_name": list,
            "symbol": "first",
            "name": "first",
            "network": "first",
            "strategies": "first",
        }
    )
    .reset_index()
)

# save the merged data
df_spaces.to_csv(PROCESSED_DATA_DIR / "spaces_gecko.csv", index=False)
