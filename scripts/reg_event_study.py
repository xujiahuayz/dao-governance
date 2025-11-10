"""Script to generate event study panel"""

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from tqdm import tqdm
from governenv.constants import (
    PROCESSED_DATA_DIR,
    EVENT_WINDOW,
    EST_LOWER,
    EST_UPPER,
)

df_proposals_adj = pd.read_csv(PROCESSED_DATA_DIR / "proposals_with_sc_blocks.csv")
df_charts = pd.read_csv(PROCESSED_DATA_DIR / "charts.csv")
df_charts["date"] = pd.to_datetime(df_charts["date"])

# Load voter participation data
df_voter = pd.read_csv(PROCESSED_DATA_DIR / "proposals_voter.csv").drop(
    columns=["space"]
)
df_proposals_adj = df_proposals_adj.merge(df_voter, on="id", how="left")

# Load the proposals characteristics
df_proposals_char = pd.read_csv(PROCESSED_DATA_DIR / "proposals_char.csv")[
    ["id", "n_choices", "duration", "quorum", "quadratic", "weighted", "ranked_choice"]
]

# Proposal created and proposal end
for stage in ["created", "end"]:
    df_proposals_adj[stage] = pd.to_datetime(df_proposals_adj[stage])
    panel = []
    for index, row in tqdm(df_proposals_adj.iterrows(), total=len(df_proposals_adj)):
        space = row["space"]
        event_date = row[stage]

        gecko_id = row["gecko_id"]
        data = (
            df_charts[
                (df_charts["gecko_id"] == gecko_id)
                & (df_charts["date"] >= event_date - pd.Timedelta(days=-EST_LOWER))
                & (df_charts["date"] <= event_date + pd.Timedelta(days=EVENT_WINDOW))
            ]
            .sort_values("date", ascending=True)
            .copy()
        )

        # check if enough data
        if len(data) != -EST_LOWER + EVENT_WINDOW + 1:
            continue

        # # Add index from -TOTAL_WINDOW+EVENT_WINDOW-1 to EVENT_WINDOW
        data = data.sort_values("date").copy()
        data["index"] = range(EST_LOWER, EVENT_WINDOW + 1)

        # calculate the beta
        estimation_window = data[(data["index"] <= EST_UPPER)]

        # calculate the covariance of emret and eret
        cov = np.cov(estimation_window["emret"], estimation_window["eret"])[0][1]
        var = np.var(estimation_window["emret"], ddof=1)
        beta = cov / var
        alpha = (
            estimation_window["eret"].mean() - beta * estimation_window["emret"].mean()
        )

        # skip if var is zero
        if np.isclose(var, 0):
            print(f"Skip {space} on {event_date} due to zero var")
            continue

        # calculate the abnormal return
        event_window = data[
            (data["index"] >= -EVENT_WINDOW) & (data["index"] <= EVENT_WINDOW)
        ].copy()
        event_window["ar"] = event_window["eret"] - (
            alpha + beta * event_window["emret"]
        )
        event_window["car"] = event_window["ar"].cumsum()

        # Proposal identifier
        event_window["id"] = row["id"]
        event_window["space"] = space

        panel.append(event_window)

    panel = pd.concat(panel, ignore_index=True)
    for df in [df_voter, df_proposals_char]:
        panel = panel.merge(df, on="id", how="left")
    panel.to_csv(
        PROCESSED_DATA_DIR / f"event_study_panel_{stage}.csv",
        index=False,
    )

    panel.groupby("index")["car"].mean().plot()
    plt.legend()
    plt.show()
