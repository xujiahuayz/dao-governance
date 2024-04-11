import gzip
import json

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

from governenv.constants import KAIKO_PRICE_PATH, SNAPSHOT_PATH_PROPOSALS
from scripts.fetch_kaiko_price import base_assets_df


# create HHI index for each proposal's "scores" (list of floats)
def hhi_index(scores: list[float]) -> float:
    total_score = sum(scores)
    if total_score == 0:
        return np.nan
    else:
        scores = [score / total_score for score in scores]
    # calculate HHI index
    # HHI index = sum of squares of scores
    hhi = sum([score**2 for score in scores])
    return hhi


# read json file
with gzip.open(KAIKO_PRICE_PATH, "r") as f:
    price_data = json.load(f)

# read proposals
with gzip.open(SNAPSHOT_PATH_PROPOSALS, "rt") as f:
    # load data and skip duplicates
    proposal_data = [json.loads(line) for line in f]

proposals = pd.DataFrame(proposal_data)
proposals["hhi"] = proposals["scores"].apply(hhi_index)

proposals["start_time"] = pd.to_datetime(proposals["start"], unit="s")
proposals["end_time"] = pd.to_datetime(proposals["end"], unit="s")
# make a dataframe with data in float format
btc_price = pd.DataFrame(price_data["BTC"])
btc_price["price"] = btc_price["price"].astype(float)

base_asset = "UNI"
# get id from base_assets_df based on base_asset
base_asset_id = base_assets_df[base_assets_df["symbol_cleaned"] == base_asset][
    "id"
].values[0]

# get proposals for base_asset_id from proposal_data using ['space']['id']
base_asset_proposals = proposals[
    proposals["space"].apply(lambda x: x["id"]) == base_asset_id
]

# pick only top 10 based on votes or hhi
base_asset_proposals = base_asset_proposals.sort_values(by="hhi", ascending=True).head(
    8
)

# get BTC denominated price for base_asset
base_asset_price = pd.DataFrame(price_data[base_asset])
base_asset_price["price"] = base_asset_price["price"].astype(float)
base_asset_price["volume"] = base_asset_price["volume"].astype(float)
# combine BTC price and base_asset price
btc_base_asset_price = pd.merge(
    btc_price, base_asset_price, on="timestamp", suffixes=("_BTC", f"_{base_asset}")
)
btc_base_asset_price["price_in_btc"] = (
    btc_base_asset_price[f"price_{base_asset}"] / btc_base_asset_price["price_BTC"]
)
# plot price in BTC with matplotlib
btc_base_asset_price["time"] = pd.to_datetime(
    btc_base_asset_price["timestamp"], unit="ms"
)
plt.plot(btc_base_asset_price["time"], btc_base_asset_price["price_in_btc"], lw=0.3)

# set y limit to be 0 to max price
max_price = btc_base_asset_price["price_in_btc"].max()
plt.ylim(0, max_price * 1.05)
plt.ylabel(f"Price (in BTC)")


plt.xticks(rotation=45)
for i, proposal in enumerate(base_asset_proposals.itertuples()):
    # mark proposal start time with vertical line
    plt.axvline(
        proposal.start_time,
        color="g",
        linestyle="--",
        lw=0.4,
        label="proposal start" if i == 0 else None,
    )
    plt.axvline(
        proposal.end_time,
        color="r",
        linestyle="--",
        lw=0.4,
        label="proposal end" if i == 0 else None,
    )

    # color the area between start and end time
    plt.axvspan(
        proposal.start_time,
        proposal.end_time,
        color="orange",
        alpha=0.1,
    )

    # mark proposal ID vertically on the line with background color with tiny font
    # take the first and last 6 letters from proposal.ipfs as text, put ... in the middle
    label = f"{proposal.ipfs[:7]}...{proposal.ipfs[-7:]}"
    plt.text(
        proposal.start_time + (proposal.end_time - proposal.start_time) / 2,
        max_price,
        label,
        rotation=90,
        # backgroundcolor="white",
        fontsize=7,
        horizontalalignment="center",
        verticalalignment="top",
        # alpha=0.8,
        # backgroundcolor needs transparency
    )

# add legend only once
plt.legend()

# plot volume on another axis as bar chart
plt.twinx()
plt.bar(
    btc_base_asset_price["time"],
    btc_base_asset_price[f"volume_{base_asset}"],
    color="gray",
    alpha=0.5,
    width=0.1,
)

# set y label
plt.ylabel(f"Volume (in {base_asset})")


# set x limit to be 2022-09-01 to 2023-04-30
# plt.xlim(pd.Timestamp("2022-09-01"), pd.Timestamp("2023-04-30"))
