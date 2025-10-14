"""Script to preprocess_event_study_car"""

from ast import literal_eval

import pandas as pd
from governenv.constants import (
    DATA_DIR,
    PROCESSED_DATA_DIR,
    EVENT_WINDOW,
)
from governenv.utils import word_count

# Load the space with Coingecko id
df_spaces = pd.read_csv(PROCESSED_DATA_DIR / "spaces_gecko.csv")

for col in ["space_id", "space_name"]:
    df_spaces[col] = df_spaces[col].apply(literal_eval)

spaces_gecko = {
    space_id: row["coingecko"]
    for _, row in df_spaces.iterrows()
    for space_id in row["space_id"]
}

spaces_set = set(_ for _ in df_spaces["space_id"].tolist() for _ in _)

# Load the value-weighted market return
df_mkt = pd.read_csv(PROCESSED_DATA_DIR / "crypto_index.csv")
df_mkt["date"] = pd.to_datetime(df_mkt["date"])
df_mkt.sort_values(by=["date"], ascending=True, inplace=True)
df_mkt["mret"] = df_mkt["prices"].pct_change()
df_mkt.dropna(subset=["mret"], inplace=True)

# Load the Coingecko market chart data
df_charts = pd.read_csv(PROCESSED_DATA_DIR / "coingecko_charts.csv")
df_charts = df_charts.loc[df_charts["gecko_id"].isin(df_spaces["coingecko"].tolist())]
df_charts.sort_values(by=["gecko_id", "date"], ascending=True, inplace=True)
df_charts["ret"] = df_charts.groupby("gecko_id")["prices"].pct_change()
df_charts.dropna(subset=["ret"], inplace=True)
df_charts["date"] = pd.to_datetime(df_charts["date"])

# Load the risk-free rate data
df_rf = pd.read_csv(DATA_DIR / "rf.csv")
df_rf["date"] = pd.to_datetime(df_rf["date"])

# Merge the market return
df_charts = df_charts.merge(df_mkt[["date", "mret"]], on="date", how="left")
df_charts.dropna(subset=["mret"], inplace=True)

# Merge the risk-free rate
df_charts = df_charts.merge(df_rf, on="date", how="left")
df_charts.dropna(subset=["rf"], inplace=True)

# Calculate excess return
df_charts["eret"] = df_charts["ret"] - df_charts["rf"]
df_charts["emret"] = df_charts["mret"] - df_charts["rf"]

# Load the proposal data
df_proposals = pd.read_csv(PROCESSED_DATA_DIR / "proposals_spaces.csv")
for col in ["choices", "scores", "strategies", "validation"]:
    df_proposals[col] = df_proposals[col].apply(literal_eval)
df_proposals = df_proposals[df_proposals["space"].isin(set(spaces_set))]
for col in ["created", "start", "end"]:
    df_proposals[f"{col}_ts"] = df_proposals[col].astype(int)
    df_proposals[col] = pd.to_datetime(df_proposals[col], unit="s").dt.strftime(
        "%Y-%m-%d"
    )
    df_proposals[col] = pd.to_datetime(df_proposals[col])
df_proposals["gecko_id"] = df_proposals["space"].map(spaces_gecko)
df_proposals.sort_values(by=["gecko_id", "created"], ascending=True, inplace=True)

# check duplicate event windows
df_proposals["last_end"] = df_proposals.groupby("gecko_id")["end"].shift(1)
df_proposals["next_created"] = df_proposals.groupby("gecko_id")["created"].shift(-1)
df_proposals["last_overlap"] = df_proposals["last_end"] + pd.Timedelta(
    days=EVENT_WINDOW
) >= df_proposals["created"] - pd.Timedelta(days=EVENT_WINDOW)
df_proposals["next_overlap"] = df_proposals["next_created"] - pd.Timedelta(
    days=EVENT_WINDOW
) <= df_proposals["end"] + pd.Timedelta(days=EVENT_WINDOW)
df_proposals_adj = df_proposals[
    ~(df_proposals["last_overlap"] | df_proposals["next_overlap"])
].copy()

# Text characteristics
for val in ["title", "body"]:
    df_proposals_adj[f"len_{val}"] = df_proposals_adj[val].apply(word_count)
df_proposals_adj["have_discussion"] = df_proposals_adj["discussion"].notna().astype(int)

# get the timestamp for event window
df_proposals_adj_ts = []
for _, row in df_proposals_adj.iterrows():
    for col in ["start", "end", "created"]:
        row[f"{col}_ts_-5d"] = row[f"{col}_ts"] - EVENT_WINDOW * 24 * 3600
        row[f"{col}_-5d"] = pd.to_datetime(
            pd.to_datetime(row[f"{col}_ts_-5d"], unit="s").strftime("%Y-%m-%d 00:00:00")
        )
        row[f"{col}_ts_+5d"] = row[f"{col}_ts"] + EVENT_WINDOW * 24 * 3600
        row[f"{col}_+5d"] = pd.to_datetime(
            pd.to_datetime(row[f"{col}_ts_+5d"], unit="s").strftime("%Y-%m-%d 00:00:00")
        )
    df_proposals_adj_ts.append(row)
df_proposals_adj = pd.DataFrame(df_proposals_adj_ts)

# merge the end date price
for col in ["start", "end", "created"]:
    for stage in [f"{col}_-5d", col, f"{col}_+5d"]:
        df_proposals_adj = df_proposals_adj.merge(
            df_charts[["gecko_id", "date", "prices"]].rename(
                columns={"date": stage, "prices": f"{stage}_price"}
            ),
            on=["gecko_id", stage],
            how="left",
        )
