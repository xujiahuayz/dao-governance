"""Script to merge Coingecko chart data."""

import json
import pandas as pd
from tqdm import tqdm
import numpy as np

from governenv.constants import DATA_DIR, PROCESSED_DATA_DIR


coingecko_coins = pd.read_csv(DATA_DIR / "coingecko_coins.csv")

panel = []

for idx, row in tqdm(coingecko_coins.iterrows(), total=coingecko_coins.shape[0]):
    gecko_id = row["id"]
    gecko_name = row["name"]
    gecko_symbol = row["symbol"]
    with open(
        f"{DATA_DIR}/coingecko/market_charts/{gecko_id}.json", "r", encoding="utf-8"
    ) as f:
        data = json.load(f)

    for idx, col in enumerate(["prices", "market_caps", "total_volumes"]):
        chart = pd.DataFrame(
            {
                "date": [item[0] for item in data[col]],
                col: [item[1] for item in data[col]],
            }
        )
        if idx == 0:
            charts = chart
        else:
            charts = charts.merge(chart, on="date", how="left")

    charts["date"] = pd.to_datetime(charts["date"], unit="ms")
    charts["date_str"] = charts["date"].dt.strftime("%Y-%m-%d")
    charts = (
        charts.sort_values("date", ascending=True)
        .drop_duplicates("date_str")
        .drop("date", axis=1)
        .rename(columns={"date_str": "date"})
    )
    charts["gecko_id"] = gecko_id
    charts["gecko_name"] = gecko_name
    charts["gecko_symbol"] = gecko_symbol
    panel.append(charts)

df_charts = pd.concat(panel, ignore_index=True)
df_charts["date"] = pd.to_datetime(df_charts["date"]) - pd.Timedelta(days=1)
df_charts = df_charts.loc[
    (df_charts["date"] >= "2016-01-01") & (df_charts["date"] <= "2025-09-01")
]

# check value close to zero to nan
df_charts.loc[df_charts["prices"] < 1e-6, "prices"] = np.nan
df_charts.loc[df_charts["market_caps"] < 0, "market_caps"] = np.nan
df_charts = df_charts.sort_values(["gecko_id", "date"])
df_charts["prices"] = df_charts.groupby("gecko_id")["prices"].ffill()
df_charts["market_caps"] = df_charts.groupby("gecko_id")["market_caps"].ffill()
df_charts.dropna(subset=["prices", "market_caps"], inplace=True)

df_charts.to_csv(PROCESSED_DATA_DIR / "coingecko_charts.csv", index=False)

# calculate the market cap weighted average price
df_charts["mcap_sum"] = df_charts.groupby("date")["market_caps"].transform("sum")
df_charts["price_mcap"] = (
    df_charts["prices"] * df_charts["market_caps"] / df_charts["mcap_sum"]
)
df_charts_weighted = (
    df_charts.groupby("date")[["price_mcap"]]
    .sum()
    .reset_index()
    .rename(columns={"price_mcap": "prices"})
)
df_charts_weighted.to_csv(PROCESSED_DATA_DIR / "crypto_index.csv", index=False)
