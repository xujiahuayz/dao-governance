"""Script to process delegation data."""

import gzip
import json

import pandas as pd
from tqdm import tqdm

from scripts.process_event_study import df_proposals_adj
from governenv.constants import DATA_DIR, PROCESSED_DATA_DIR

snapshot_delegate = []
with gzip.open(DATA_DIR / "snapshot_delegate.jsonl.gz", "rt", encoding="utf-8") as f:
    for line in f:
        snapshot_delegate.append(json.loads(line))


df_delegate = pd.DataFrame(
    [_ for _ in snapshot_delegate if _["space"] in df_proposals_adj["space"].unique()]
)

df_delegation = []

for space in tqdm(df_delegate["space"].unique()):
    group = df_delegate.loc[df_delegate["space"] == space].copy()
    space_proposals = df_proposals_adj.loc[
        df_proposals_adj["space"] == space
    ].sort_values(by="created", ascending=True)

    # Aggregate votes for a space
    df_votes = []
    for proposal in space_proposals["id"].unique():
        try:
            with open(
                DATA_DIR / "snapshot" / "votes" / f"{proposal}.jsonl",
                "r",
                encoding="utf-8",
            ) as f:
                df_vote = pd.DataFrame([json.loads(line) for line in f])
                df_vote["proposal"] = proposal

            df_votes.append(df_vote)
        except FileNotFoundError:
            continue
    df_votes = pd.concat(df_votes, ignore_index=True)
    df_votes.sort_values(by=["created"], ascending=True, inplace=True)
    df_votes["voter"] = df_votes["voter"].str.lower()

    for index, row in group.iterrows():
        timestamp = row["timestamp"]
        space = row["space"]
        delegator = row["delegator"]
        delegate = row["delegate"]

        votes_after_delegation = df_votes[
            (df_votes["voter"] == delegator) & (df_votes["created"] > timestamp)
        ].sort_values(by="created", ascending=True)

        ts_votes_after_delegation = (
            int(votes_after_delegation.iloc[0]["created"])
            if len(votes_after_delegation) > 0
            else None
        )

        df_delegation.append(
            {
                "space": space,
                "delegator": delegator,
                "delegate": delegate,
                "timestamp": timestamp,
                "ts_votes_after_delegation": ts_votes_after_delegation,
            }
        )

df_delegation = pd.DataFrame(df_delegation)
for col in ["timestamp", "ts_votes_after_delegation"]:
    df_delegation[col] = pd.to_datetime(df_delegation[col], unit="s")

df = df_proposals_adj.copy()
panel_delegate = []
for idx, row in tqdm(df.iterrows(), total=len(df)):

    delegates_before_end = df_delegation[
        (df_delegation["space"] == row["space"])
        & (df_delegation["timestamp"] <= row["end"])
        & (df_delegation["timestamp"] >= row["created"])
        & (
            (df_delegation["ts_votes_after_delegation"].isna())
            | (df_delegation["ts_votes_after_delegation"] > row["end"])
        )
    ].copy()

    row["delegate"] = len(delegates_before_end["delegator"].unique())
    panel_delegate.append(row)

df_panel_delegate = pd.DataFrame(panel_delegate)
df_panel_delegate["delegate_dummy"] = (df_panel_delegate["delegate"] > 0).apply(int)
df_panel_delegate.to_csv(
    PROCESSED_DATA_DIR / "proposals_adjusted_delegates.csv", index=False
)
