"""Script to process discussion panel (ALL valid 0->1 switches with clean windows)"""

import matplotlib.pyplot as plt
import pandas as pd
from governenv.constants import PROCESSED_DATA_DIR

PERIOD = 6

# Load + basic cleaning
df_proposals = pd.read_csv(PROCESSED_DATA_DIR / "proposals_panel.csv")
df_proposals["date"] = pd.to_datetime(df_proposals["date"])
df_proposals["have_discussion"] = df_proposals["have_discussion"].fillna(0).astype(int)

df_proposals.sort_values(by=["space", "date"], ascending=True, inplace=True)

# Identify space types
all_discussion_space = set()
no_discussion_space = set()
switching_space = set()

for space, group in df_proposals.groupby("space"):
    s = group["have_discussion"]
    if s.sum() == len(s):
        all_discussion_space.add(space)
    elif s.sum() == 0:
        no_discussion_space.add(space)
    else:
        switching_space.add(space)

df_keep = df_proposals[
    df_proposals["space"].isin(switching_space.union(all_discussion_space))
].copy()

df_keep["treat"] = df_keep["space"].apply(lambda x: 1 if x in switching_space else 0)

# Add proposal_id within each space
indexed = []
for space, group in df_keep.groupby("space"):
    g = group.sort_values("date").copy()
    g.reset_index(drop=True, inplace=True)
    g["proposal_id"] = range(len(g))
    indexed.append(g)

df_keep = pd.concat(indexed, ignore_index=True)


# Helper: find all valid switch indices in a space
def find_valid_switches(g: pd.DataFrame, period: int) -> list[int]:
    """
    Return all treat_index t such that:
      - t is a true 0->1 switch (g[t-1]=0 and g[t]=1)
      - pre window [t-period, t-1] exists and all 0
      - post window [t, t+period] exists and all 1
    Assumes g has proposal_id 0..n-1 and is sorted by proposal_id.
    """
    n = len(g)
    s = g["have_discussion"].to_numpy()

    valid = []
    for t in range(1, n):  # t must have t-1
        # must have full windows
        if t - period < 0:
            continue
        if t + period >= n:
            continue

        # true switch 0->1 at boundary
        if not (s[t - 1] == 0 and s[t] == 1):
            continue

        pre = s[(t - period) : t]  # length = period
        post = s[t : (t + period + 1)]  # length = period+1

        # if (pre == 0).all() and (post == 1).all():
        valid.append(t)

    return valid


# Build DID/event-study panel
panel = {
    "event_time": [],
    "space": [],
    "time": [],
    "treat": [],
    "post": [],
    "cohort": [],
    "non_whale_participation": [],
    "whale_participation": [],
    "token": [],
}

treated_spaces = df_keep.loc[df_keep["treat"] == 1, "space"].unique().tolist()
control_spaces = df_keep.loc[df_keep["treat"] == 0, "space"].unique().tolist()

for space in treated_spaces:
    g = df_keep[df_keep["space"] == space].sort_values("proposal_id").copy()
    g.reset_index(drop=True, inplace=True)

    treat_indices = find_valid_switches(g, PERIOD)
    if len(treat_indices) == 0:
        continue

    for treat_index in treat_indices:
        cohort_id = f"{space}__{treat_index}"

        # treated rows: event window
        g_win = g[
            g["proposal_id"].between(treat_index - PERIOD, treat_index + PERIOD)
        ].copy()
        # sanity: should be exactly (2*PERIOD+1)
        if len(g_win) != (2 * PERIOD + 1):
            continue

        # add treated observations
        for _, row in g_win.iterrows():
            et = int(row["proposal_id"] - treat_index)  # -PERIOD .. +PERIOD
            panel["space"].append(space)
            panel["event_time"].append(et)
            panel["time"].append(int(row["proposal_id"]))
            panel["treat"].append(1)
            panel["post"].append(1 if et >= 0 else 0)
            panel["cohort"].append(cohort_id)
            panel["non_whale_participation"].append(row["non_whale_participation"])
            panel["whale_participation"].append(row["whale_participation"])
            panel["token"].append(row["gecko_id"])

        # controls: align by event_time using all-discussion spaces
        # For each control space, we need proposal_id range [treat_index-PERIOD, treat_index+PERIOD] to exist.
        df_control = df_keep[
            (df_keep["treat"] == 0)
            & (df_keep["proposal_id"] >= treat_index - PERIOD)
            & (df_keep["proposal_id"] <= treat_index + PERIOD)
        ].copy()

        # add control observations
        for _, row in df_control.iterrows():
            et = int(row["proposal_id"] - treat_index)
            panel["space"].append(row["space"])
            panel["event_time"].append(et)
            panel["time"].append(int(row["proposal_id"]))
            panel["treat"].append(0)
            panel["post"].append(1 if et >= 0 else 0)
            panel["cohort"].append(cohort_id)  # align to treated event
            panel["non_whale_participation"].append(row["non_whale_participation"])
            panel["whale_participation"].append(row["whale_participation"])
            panel["token"].append(row["gecko_id"])

df_did_panel = pd.DataFrame(panel)

# Quick plot (avg by event_time)
plt.figure(figsize=(10, 6))

treat_mean = (
    df_did_panel.loc[df_did_panel["treat"] == 1]
    .groupby("event_time")["non_whale_participation"]
    .mean()
    .sort_index()
)
ctrl_mean = (
    df_did_panel.loc[df_did_panel["treat"] == 0]
    .groupby("event_time")["non_whale_participation"]
    .mean()
    .sort_index()
)

plt.plot(treat_mean.index, treat_mean.values, label="Treatment")
plt.plot(ctrl_mean.index, ctrl_mean.values, label="Control (all-discussion spaces)")

plt.axvline(x=-0.5, color="red", linestyle="--")
plt.legend()
plt.tight_layout()
plt.show()

# Save
out_path = PROCESSED_DATA_DIR / "reg_did_discussion.csv"
df_did_panel.to_csv(out_path, index=False)

print("Saved:", out_path)
print(
    "Unique treated events (cohorts):",
    df_did_panel.loc[df_did_panel["treat"] == 1, "cohort"].nunique(),
)
print("Rows:", len(df_did_panel))
