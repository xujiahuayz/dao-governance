"""Script to process delegation data."""

import gzip
import json

import pandas as pd
from tqdm import tqdm

from governenv.constants import DATA_DIR, PROCESSED_DATA_DIR, EVENT_WINDOW

snapshot_delegate = []
with gzip.open(DATA_DIR / "snapshot_delegate.jsonl.gz", "rt", encoding="utf-8") as f:
    for line in f:
        snapshot_delegate.append(json.loads(line))

panel_created = pd.read_csv(PROCESSED_DATA_DIR / "event_study_panel_created.csv")
panel_end = pd.read_csv(PROCESSED_DATA_DIR / "event_study_panel_end.csv")

df_delegate = pd.DataFrame(
    [_ for _ in snapshot_delegate if _["space"] in panel_created["space"].unique()]
)

df_delegation = []

for space in tqdm(df_delegate["space"].unique()):
    group = df_delegate.loc[df_delegate["space"] == space].copy()
    space_proposals = panel_created.loc[panel_created["space"] == space].sort_values(
        by="created", ascending=True
    )

    # Aggregate votes for a space
    df_votes = []
    for proposal in space_proposals["id"].unique():
        with open(
            DATA_DIR / "snapshot" / "votes" / f"{proposal}.jsonl",
            "r",
            encoding="utf-8",
        ) as f:
            df_vote = pd.DataFrame([json.loads(line) for line in f])
            df_vote["proposal"] = proposal

        df_votes.append(df_vote)
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

for name, df in [("created", panel_created), ("end", panel_end)]:
    df = df.loc[df["index"] == EVENT_WINDOW].copy()
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
    df_panel_delegate["delegate"] = (df_panel_delegate["delegate"] > 0).apply(int)
    df_panel_delegate.to_csv(
        PROCESSED_DATA_DIR / f"event_study_panel_{name}_delegate.csv", index=False
    )
