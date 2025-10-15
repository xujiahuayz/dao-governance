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
from scripts.process_event_study import (
    df_charts,
    df_proposals_adj,
)

# Load the vote characteristics
VOTING_CHARACTERISTICS = ["half_vp_ratio", "vn_hhi", "vs_hhi", "cci"]
df_votes = pd.read_csv(PROCESSED_DATA_DIR / "proposals_adjusted_votes.csv")
df_votes = df_votes[["id"] + VOTING_CHARACTERISTICS + ["reject_pct", "binary"]]

# Proposal created and proposal end
for stage in ["created", "end"]:
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

        # calculate the cumulative abnormal return
        for window in (2, 3, 4, 5):
            df = event_window.loc[
                event_window["index"].between(-window, window)
            ].sort_values("index")
            df[f"car_{window}"] = df["ar"].cumsum()
            event_window = event_window.merge(
                df[["index", f"car_{window}"]],
                on="index",
                how="left",
            )

        # event_window["car"] = event_window["ar"].cumsum()

        # Proposal identifier
        event_window["id"] = row["id"]
        event_window["space"] = space

        panel.append(event_window)

    panel = pd.concat(panel, ignore_index=True)
    panel = panel.merge(
        df_votes,
        on="id",
        how="left",
    )

    # # winsorized all variables
    # for var in ["car"] + VOTING_CHARACTERISTICS:
    #     lower = panel[var].quantile(0.01)
    #     upper = panel[var].quantile(0.99)
    #     panel[var] = np.where(panel[var] < lower, lower, panel[var])
    #     panel[var] = np.where(panel[var] > upper, upper, panel[var])

    panel.to_csv(
        PROCESSED_DATA_DIR / f"event_study_panel_{stage}.csv",
        index=False,
    )

    # panel.groupby("index")["car"].mean().plot()
    # plt.legend()
    # plt.plot()
