"""Script to process delegation panel"""

import matplotlib.pyplot as plt
import pandas as pd
from governenv.constants import PROCESSED_DATA_DIR

PERIOD = 6

df_proposals = pd.read_csv(PROCESSED_DATA_DIR / "proposals_panel.csv")
df_proposals.sort_values(by=["space", "date"], ascending=True, inplace=True)

# Identify treatment groups
delegation_space = set(
    df_proposals.loc[df_proposals["delegation"] == 1, "space"].tolist()
)
nodelegation_space = set(
    df_proposals.loc[df_proposals["delegation"] == 0, "space"].tolist()
)
both = delegation_space.intersection(nodelegation_space)

# Remove the all delegation spaces
df_proposals = df_proposals[
    (df_proposals["space"].isin(both)) | (df_proposals["delegation"] == 0)
].copy()

df_proposals["treat"] = df_proposals["space"].apply(lambda x: 1 if x in both else 0)

# Add index for each space
df_proposals_indexed = []
for _, group in df_proposals.groupby("space"):
    group = group.copy()
    group.sort_values(by="date", ascending=True, inplace=True)
    group.reset_index(drop=True, inplace=True)
    group["proposal_id"] = range(len(group))
    df_proposals_indexed.append(group)

df_proposals = pd.concat(df_proposals_indexed, ignore_index=True)

# Iterate through treatment groups to build DID panel
panel = {
    "event_time": [],
    "space": [],
    "time": [],
    "treat": [],
    "post": [],
    "cohort": [],
    "control_cohort": [],
    "non_whale_participation": [],
    "whale_participation": [],
}

for idx, (space, group) in enumerate(
    df_proposals.loc[df_proposals["treat"] == 1].groupby("space")
):

    group = group.copy()
    # isolate the last five non-delegation proposals and first five delegation proposals
    df_nodelegation = (
        group.loc[group["delegation"] == 0]
        .sort_values(by="date", ascending=False)
        .head(PERIOD)
    )
    df_delegation_only = (
        group.loc[group["delegation"] == 1]
        .sort_values(by="date", ascending=True)
        .head(PERIOD + 1)
    )

    # get the index of the proposal where delegation is first introduced
    treat_index = df_delegation_only["proposal_id"].min()

    # assign index
    for i, (_, row) in enumerate(df_nodelegation.iterrows()):
        panel["space"].append(row["space"])
        panel["event_time"].append(-i - 1)  # assign id -5 to -1
        panel["time"].append(row["proposal_id"])
        panel["treat"].append(1)
        panel["post"].append(0)
        panel["cohort"].append(treat_index)
        panel["control_cohort"].append(treat_index)
        panel["non_whale_participation"].append(row["non_whale_participation"])
        panel["whale_participation"].append(row["whale_participation"])

    for i, (_, row) in enumerate(df_delegation_only.iterrows()):
        panel["space"].append(row["space"])
        panel["event_time"].append(i)  # assign id 0 to 5
        panel["time"].append(row["proposal_id"])
        panel["treat"].append(1)
        panel["post"].append(1)
        panel["cohort"].append(treat_index)
        panel["control_cohort"].append(treat_index)
        panel["non_whale_participation"].append(row["non_whale_participation"])
        panel["whale_participation"].append(row["whale_participation"])

    # isolate corresponding control proposals
    df_control = df_proposals[
        (df_proposals["treat"] == 0)
        & (df_proposals["proposal_id"] >= treat_index - PERIOD)
        & (df_proposals["proposal_id"] <= treat_index + PERIOD)
    ]
    print("space:", space, "index:", treat_index, "control proposals:", len(df_control))
    for _, row in df_control.iterrows():
        panel["space"].append(row["space"])
        panel["event_time"].append(row["proposal_id"] - treat_index)
        panel["time"].append(row["proposal_id"])
        panel["treat"].append(0)
        panel["post"].append(1 if row["proposal_id"] >= treat_index else 0)
        panel["cohort"].append(treat_index)
        panel["control_cohort"].append(9999)
        panel["non_whale_participation"].append(row["non_whale_participation"])
        panel["whale_participation"].append(row["whale_participation"])

df_did_panel = pd.DataFrame(panel)

plt.figure(figsize=(10, 6))
# plt.plot(
#     df_did_panel.loc[df_did_panel["treat"] == 1]
#     .groupby("event_time")["non_whale_participation"]
#     .mean(),
#     label="Treatment",
# )
# plt.plot(
#     df_did_panel.loc[df_did_panel["treat"] == 0]
#     .groupby("event_time")["non_whale_participation"]
#     .mean(),
#     label="Control",
# )
plt.plot(
    df_did_panel.loc[df_did_panel["treat"] == 1]
    .groupby("event_time")["non_whale_participation"]
    .mean()
    - df_did_panel.loc[df_did_panel["treat"] == 0]
    .groupby("event_time")["non_whale_participation"]
    .mean(),
    label="Difference",
)
plt.axvline(x=-0.5, color="red", linestyle="--")
plt.legend()
plt.show()

df_did_panel.to_csv(PROCESSED_DATA_DIR / "reg_did_delegation.csv", index=False)
