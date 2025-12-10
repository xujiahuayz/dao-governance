"""Script to generate event study panel"""

import numpy as np
import pandas as pd
from governenv.constants import (
    PROCESSED_DATA_DIR,
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
    "have_discussion",
    "delegation",
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
    "discussion_created",
]


df_proposals = pd.read_csv(PROCESSED_DATA_DIR / "proposals_with_sc_blocks.csv").drop(
    columns=["quorum", "have_discussion", "delegation"]
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

# Load the user characteristics
df_user = pd.read_csv(PROCESSED_DATA_DIR / "proposal_user.csv")[["id"] + USER_CHAR]

# Remove proposal without infrastructure
df_user.replace({0: np.nan}, inplace=True)

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
]:
    df_proposals = df_proposals.merge(df, on="id", how="left")

df_proposals["date"] = pd.to_datetime(df_proposals["created"])
df_proposals = df_proposals[
    ["space", "gecko_id", "date"]
    + WIN_CHAR
    + PROPOSALS_CHAR
    + TOPIC_COLUMNS
    + USER_CHAR
    + DISCUSSION_CHAR
]

# Identify treatment groups
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

df_proposals.to_csv(PROCESSED_DATA_DIR / "proposals_panel.csv", index=False)
