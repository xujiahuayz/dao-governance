"""Script to generate event study panel"""

import pandas as pd
from governenv.constants import (
    PROCESSED_DATA_DIR,
    TOPICS,
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

for df in [df_voter, df_proposals_char, df_proposals_topic]:
    df_proposals = df_proposals.merge(df, on="id", how="left")

df_proposals["date"] = pd.to_datetime(df_proposals["created"])
df_proposals = df_proposals[
    ["space", "gecko_id", "date"] + WIN_CHAR + PROPOSALS_CHAR + TOPIC_COLUMNS
]


df_proposals.to_csv(PROCESSED_DATA_DIR / "proposals_panel.csv", index=False)
