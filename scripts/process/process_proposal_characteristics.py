"""Script to process proposal data for regression analysis."""

from ast import literal_eval
import pandas as pd

from governenv.constants import PROCESSED_DATA_DIR

df_proposals = pd.read_csv(PROCESSED_DATA_DIR / "proposals_with_sc_blocks.csv")
for col in ["created", "start", "end"]:
    df_proposals[col] = pd.to_datetime(df_proposals[col])

for col in ["choices"]:
    df_proposals[col] = df_proposals[col].apply(literal_eval)

df_proposals["n_choices"] = df_proposals.apply(lambda x: len(x["choices"]), axis=1)
df_proposals["multi_choices"] = df_proposals.apply(
    lambda x: 1 if len(x["choices"]) > 2 else 0, axis=1
)
df_proposals["duration"] = (df_proposals["end"] - df_proposals["created"]).dt.days
df_proposals["quadratic"] = (df_proposals["type"] == "quadratic").astype(int)
df_proposals["weighted"] = (df_proposals["type"] == "weighted").astype(int)
df_proposals["ranked_choice"] = (df_proposals["type"] == "ranked-choice").astype(int)
df_proposals["have_discussion"] = df_proposals["discussion"].apply(
    lambda x: 0 if pd.isna(x) else 1
)
df_proposals["quorum"] = df_proposals["quorum"].apply(lambda x: 1 if x != 0 else 0)
df_proposals["delegation"] = df_proposals["delegation"].apply(
    lambda x: 1 if x == "delegation" else 0
)

df_proposals.to_csv(PROCESSED_DATA_DIR / "proposals_char.csv", index=False)
