"""Script to generate the fee DID panel"""

import ast
import warnings
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from tqdm import tqdm
from governenv.constants import PROCESSED_DATA_DIR

warnings.filterwarnings("ignore")

EVENT_WINDOW = 10

# Load the space with defillama fee data
df_spaces = pd.read_csv(PROCESSED_DATA_DIR / "spaces_defillama_fees.csv")

for col in ["space_id", "slug"]:
    df_spaces[col] = df_spaces[col].apply(ast.literal_eval)

fee_protocols = set(
    space_id
    for space_id_list in df_spaces["space_id"].tolist()
    for space_id in space_id_list
)
treat_mslug = set(df_spaces["mslug"].tolist())

treat_mslug_space_id = dict(
    (mslug, space_id_list)
    for mslug, space_id_list in zip(df_spaces["mslug"], df_spaces["space_id"])
)

treat_space_id_mslug = {}
for k, v in treat_mslug_space_id.items():
    for space_id in v:
        treat_space_id_mslug[space_id] = k


# Load the fee data
df_fees = pd.read_csv(PROCESSED_DATA_DIR / "fees.csv")
df_fees["date"] = pd.to_datetime(df_fees["date"]).dt.strftime("%Y-%m-%d")
df_fees["date"] = pd.to_datetime(df_fees["date"])
df_fees.sort_values(by=["mslug", "date"], ascending=True, inplace=True)

# Load the proposal data
proposals = pd.read_csv(PROCESSED_DATA_DIR / "proposals_spaces.csv")
proposals = proposals[proposals["space"].isin(fee_protocols)]
for col in ["start", "end"]:
    proposals[col] = pd.to_datetime(proposals[col], unit="s").dt.strftime("%Y-%m-%d")
    proposals[col] = pd.to_datetime(proposals[col])
# proposals.drop_duplicates(subset=["space", "end"], inplace=True)

# check duplicate event windows
proposals.sort_values(by=["space", "start"], ascending=True, inplace=True)
proposals["last_end"] = proposals.groupby("space")["end"].shift(1)
proposals["next_start"] = proposals.groupby("space")["start"].shift(-1)
proposals["last_overlap"] = proposals["last_end"] + pd.Timedelta(
    days=EVENT_WINDOW
) >= proposals["start"] - pd.Timedelta(days=EVENT_WINDOW)
proposals["next_overlap"] = proposals["next_start"] - pd.Timedelta(
    days=EVENT_WINDOW
) <= proposals["end"] + pd.Timedelta(days=EVENT_WINDOW)
proposals_adj = proposals[~(proposals["last_overlap"] | proposals["next_overlap"])]
treat_set = set(proposals["space"].tolist())


panel = []
cohort_idx = 0

for end_date, group in tqdm(proposals_adj.groupby("end")):
    # meta information
    cohort_idx += 1
    event_time = end_date
    treat_spaces_id = set(group["space"].tolist())

    # select cohort control
    cohort_control = df_fees[
        (df_fees["date"] >= event_time - pd.Timedelta(days=EVENT_WINDOW))
        & (df_fees["date"] <= event_time + pd.Timedelta(days=EVENT_WINDOW))
        & (~df_fees["mslug"].isin(treat_mslug))
    ]

    # select cohort treat
    treat_mslug_end_date = set(treat_space_id_mslug[_] for _ in treat_spaces_id)
    cohort_treat = df_fees[
        (df_fees["date"] >= event_time - pd.Timedelta(days=EVENT_WINDOW))
        & (df_fees["date"] <= event_time + pd.Timedelta(days=EVENT_WINDOW))
        & (df_fees["mslug"].isin(treat_mslug_end_date))
    ]

    # merge cohort
    cohort = pd.concat([cohort_control, cohort_treat], ignore_index=True)

    # Add treat
    cohort["treat"] = cohort["mslug"].apply(
        lambda x: 1 if x in treat_mslug_end_date else 0
    )

    # Add post
    cohort["post"] = (cohort["date"] >= event_time).astype(int)

    # Add cohort index
    cohort["cohort"] = cohort_idx

    # Add time index
    cohort["time"] = event_time

    # relative event day (can bucket later for event-study)
    cohort["event_day"] = (cohort["date"] - event_time).dt.days

    panel.append(cohort)

panel = pd.concat(panel, ignore_index=True)
panel.rename(columns={"mslug": "protocol"}, inplace=True)
panel["log_fee"] = np.log(panel["fee"] + 1)

treat = panel.loc[panel["treat"] == 1]

control = panel.loc[panel["treat"] == 0]
plt.plot(
    treat.groupby("event_day")["log_fee"].mean()
    - control.groupby("event_day")["log_fee"].mean()
)
plt.legend()
plt.show()
