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
    TOPICS,
    CRITERIA,
)

VOTE_CHAR = [
    "non_whale_victory_vn",
    "non_whale_victory_vp",
    "non_whale_victory_vp_vn",
    "non_whale_turnout",
    "whale_turnout",
]

PROPOSAL_CHAR = [
    "n_choices",
    "duration",
    "quorum",
    "quadratic",
    "weighted",
    "ranked_choice",
]
DISCUSSION_CHAR = [
    *[_.lower().replace(" ", "_") for _ in CRITERIA],
    "reply_number",
    "view_number",
    "like_number",
    "post_number",
    "hhi_post_number",
    "hhi_word_count",
    "discussion_created",
]

TOPIC_COLUMNS = [topic.replace(" ", "_") for topic in TOPICS]

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

# Load topic characteristics
df_proposals_topic = pd.read_csv(PROCESSED_DATA_DIR / "proposals_topic.csv")[
    ["id"] + TOPIC_COLUMNS
]

# Load discussion characteristics
df_proposals_discussion = pd.read_csv(
    PROCESSED_DATA_DIR / "proposals_discussion_char.csv"
)[["id"] + DISCUSSION_CHAR]

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
        event_window["beta"] = beta
        event_window["car"] = event_window["ar"].cumsum()

        # Identifiers
        event_window["space"] = space
        event_window["id"] = row["id"]

        panel.append(event_window)

    panel = pd.concat(panel, ignore_index=True)
    for df in [
        df_voter,
        df_proposals_char,
        df_proposals_topic,
        df_proposals_discussion,
    ]:
        panel = panel.merge(df, on="id", how="left")

    panel = panel[
        ["id", "gecko_id", "space", "date", "index", "car"]
        + VOTE_CHAR
        + PROPOSAL_CHAR
        + TOPIC_COLUMNS
        + DISCUSSION_CHAR
    ]
    panel.to_csv(
        PROCESSED_DATA_DIR / f"event_study_panel_{stage}.csv",
        index=False,
    )

    panel.groupby("index")["car"].mean().plot()
    plt.legend()
    plt.show()
