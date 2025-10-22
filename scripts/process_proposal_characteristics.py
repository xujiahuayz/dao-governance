"""Script to process proposal data for regression analysis."""

import numpy as np

from scripts.process_event_study import df_proposals_adj
from governenv.constants import PROCESSED_DATA_DIR

df_proposals_adj["votes"] = np.log(df_proposals_adj["votes"] + 1)
df_proposals_adj["n_choices"] = df_proposals_adj["choices"].apply(len)
df_proposals_adj["duration"] = (
    df_proposals_adj["end"] - df_proposals_adj["created"]
).dt.days
df_proposals_adj["quadratic"] = (df_proposals_adj["type"] == "quadratic").astype(int)
df_proposals_adj["ranked_choice"] = (
    df_proposals_adj["type"] == "ranked-choice"
).astype(int)

df_proposals_adj["choices"] = df_proposals_adj["choices"].apply(
    lambda choices: [choice.lower() for choice in choices]
)
df_proposals_adj["quorum"] = df_proposals_adj["quorum"].apply(
    lambda x: 1 if x != 0 else 0
)

df_proposals_adj.to_csv(
    PROCESSED_DATA_DIR / "proposals_adjusted_proposals.csv", index=False
)
