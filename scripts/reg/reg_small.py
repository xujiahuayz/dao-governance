"""Script to generate event study panel"""

import gzip
import json
import numpy as np
import pandas as pd
from governenv.constants import (
    PROCESSED_DATA_DIR,
    SNAPSHOT_PATH,
    TOPICS,
    CRITERIA,
)

IDENTIFIERS = ["id", "space", "gecko_id", "date"]
WIN_CHAR = [
    "non_whale_victory_vp",
    "non_whale_victory_vn",
    "non_whale_victory_vp_vn",
    "non_whale_from_delegation_rate",
    "whale_from_delegation_rate",
    "non_whale_to_delegation_rate",
    "whale_to_delegation_rate",
    "whale_vs_hhi",
    "non_whale_vs_hhi",
    "whale_vn_hhi",
    "non_whale_vn_hhi",
    "non_whale_turnout",
    "whale_turnout",
    "non_whale_participation",
    "whale_participation",
]
PROPOSALS_CHAR = [
    "n_choices",
    "multi_choices",
    "duration",
    "quadratic",
    "weighted",
    "ranked_choice",
    "quorum",
    "delegation",
    "have_discussion",
]
TOPIC_COLUMNS = [topic.replace(" ", "_") for topic in TOPICS]
USER_CHAR = ["voter_user", "whale_user", "non_whale_user"]
DISCUSSION_CHAR = [
    *[_.lower().replace(" ", "_") for _ in CRITERIA],
    "reply_number",
    "view_number",
    "like_number",
    "post_number",
    "hhi_post_number",
    "hhi_word_count",
]
CAR_CHAR = [
    "car_created",
    "car_end",
]
SPACE_CHAR = ["categories", "network"]
BEFORE_AFTER_CHAR = [
    "concensus_after",
    "concensus_full",
    "concensus_before",
]

df_proposals = pd.read_csv(PROCESSED_DATA_DIR / "proposals_with_sc_blocks.csv").drop(
    columns=["quorum", "have_discussion", "delegation"]
)

# Load the space data
with gzip.open(SNAPSHOT_PATH, "rt") as f:
    # load data and skip duplicates
    spaces = [json.loads(line) for line in f]

# keep proposal number is not None, > 0, has coingecko id, and verified
spaces = [
    item
    for item in spaces
    if (item["proposalsCount"] is not None)
    and (item["proposalsCount"] > 0)
    and (item["coingecko"] is not None)
    and item["verified"]
]
df_spaces = pd.DataFrame(spaces).rename(columns={"id": "space", "name": "space_name"})[
    ["space", "categories"]
]

df_spaces["categories"] = df_spaces["categories"].apply(
    lambda x: x[0] if len(x) > 0 else "other"
)

# Load voter participation data
df_voter = pd.read_csv(PROCESSED_DATA_DIR / "proposals_voter.csv")[["id"] + WIN_CHAR]

# Load the proposals characteristics
df_proposals_char = pd.read_csv(PROCESSED_DATA_DIR / "proposals_char.csv")[
    ["id"] + PROPOSALS_CHAR
]

# Load topic characteristics
df_proposals_topic = pd.read_csv(PROCESSED_DATA_DIR / "proposals_topic.csv")[
    ["id"] + TOPIC_COLUMNS
]

# Load before and after discussion characteristics
df_proposals_before_after = pd.read_csv(
    PROCESSED_DATA_DIR / "proposals_before_after_discussion.csv"
)[["id"] + BEFORE_AFTER_CHAR]

# Load CAR
df_car_created = pd.read_csv(PROCESSED_DATA_DIR / "event_study_panel_created.csv")[
    ["id", "car", "index"]
].rename(columns={"car": "car_created"})
df_car_created = df_car_created.loc[df_car_created["index"] == 5, ["id", "car_created"]]

df_car_end = pd.read_csv(PROCESSED_DATA_DIR / "event_study_panel_end.csv")[
    ["id", "car", "index"]
].rename(columns={"car": "car_end"})
df_car_end = df_car_end.loc[df_car_end["index"] == 5, ["id", "car_end"]]

# Load the user characteristics
df_user = pd.read_csv(PROCESSED_DATA_DIR / "proposal_user.csv")[
    ["id", "space"] + USER_CHAR
]

# Remove users in spaces without infrastructure
df_user["infrastructure"] = (
    df_user.groupby("space")["voter_user"].transform("sum").gt(0).astype(int)
)
# df_user.loc[df_user["infrastructure"] == 0, USER_CHAR] = np.nan
USER_CHAR.append("infrastructure")
df_user = df_user.drop(columns=["space"])

# Load the discussion characteristics
df_proposals_discussion = pd.read_csv(
    PROCESSED_DATA_DIR / "proposals_discussion_char.csv"
)[["id"] + DISCUSSION_CHAR]

for df in [
    df_voter,
    df_proposals_char,
    df_proposals_topic,
    df_user,
    df_proposals_discussion,
    df_car_created,
    df_car_end,
    df_proposals_before_after,
]:
    df_proposals = df_proposals.merge(df, on="id", how="left")

# Merge with space characteristics
df_proposals = df_proposals.merge(df_spaces, on="space", how="left")

df_proposals["date"] = pd.to_datetime(df_proposals["created"])
df_proposals = df_proposals[
    ["space", "gecko_id", "date", "id"]
    + WIN_CHAR
    + PROPOSALS_CHAR
    + TOPIC_COLUMNS
    + USER_CHAR
    + DISCUSSION_CHAR
    + CAR_CHAR
    + SPACE_CHAR
    + BEFORE_AFTER_CHAR
]

# Fillna the infrastructure with 0
df_proposals["infrastructure"] = df_proposals["infrastructure"].fillna(0).astype(int)

# Identify delegation treatment groups
delegation_space = set(
    df_proposals.loc[df_proposals["delegation"] == 1, "space"].tolist()
)
nodelegation_space = set(
    df_proposals.loc[df_proposals["delegation"] == 0, "space"].tolist()
)
both = delegation_space.intersection(nodelegation_space)
df_proposals["switch_delegation"] = df_proposals["space"].apply(
    lambda x: 1 if x in both else 0
)

# Identify discussion treatment groups
df_proposals["have_discussion"] = df_proposals["have_discussion"].fillna(0).astype(int)

tmp = df_proposals[["space", "date", "have_discussion"]].sort_values(["space", "date"])

# first date when discussion appears in that space
first_one_date = tmp.loc[tmp["have_discussion"] == 1].groupby("space")["date"].min()

# whether there exists a 0 before that first 1
switched_0_to_1 = (
    tmp.merge(first_one_date.rename("first_one_date"), on="space", how="left")
    .assign(
        is_zero_before_first_one=lambda x: (x["have_discussion"] == 0)
        & (x["date"] < x["first_one_date"])
    )
    .groupby("space")["is_zero_before_first_one"]
    .any()
    .fillna(False)
)

df_proposals["switch_discussion"] = (
    df_proposals["space"].map(switched_0_to_1).fillna(False).astype(int)
)

# winsorize the continuous variables at 99th percentile
for col in (
    ["non_whale_participation", "whale_participation"] + DISCUSSION_CHAR + USER_CHAR
):
    upper_bound = df_proposals[col].quantile(0.99)
    df_proposals[col] = np.where(
        df_proposals[col] > upper_bound, upper_bound, df_proposals[col]
    )

# calculate the difference between after and before discussion characteristics and split into high and low
df_proposals["concensus_diff"] = (
    df_proposals["concensus_full"] - df_proposals["concensus_before"]
)

# print(df_proposals.groupby("infrastructure")[TOPIC_COLUMNS].mean())
# print(df_proposals.loc[df_proposals["infrastructure"] == 0]["space"].nunique())
# print(df_proposals.loc[df_proposals["infrastructure"] != 0]["space"].nunique())

df_proposals["topic"] = df_proposals[TOPIC_COLUMNS].idxmax(axis=1).str.replace("_", " ")

df_proposals["have_discussion_delegation"] = (
    df_proposals["have_discussion"] * df_proposals["delegation"]
)
df_proposals["have_discussion_delegation"].value_counts()

df_proposals.to_csv(PROCESSED_DATA_DIR / "proposals_panel.csv", index=False)
