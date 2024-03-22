import json

import requests

from governenv.constants import KAIKO_PRICE_PATH
from governenv.settings import KAIKO_API_KEY
from scripts.process_spaces import df_spaces

# get id from df_spaces for the first 500 spaces

base_assets_df = df_spaces[df_spaces["proposalsCount"] >= 1].iloc[:20]

# replace veBAL with BAL, veSTG with STG, .. all "ve" prefix, remove only when ve is prefix
base_assets = base_assets_df["symbol"].tolist()

base_assets = [
    base_asset[2:] if base_asset[:2] == "ve" else base_asset
    for base_asset in base_assets
]

# remove "VOTE" suffix
base_assets = [
    base_asset[:-4] if base_asset[-4:] == "VOTE" else base_asset
    for base_asset in base_assets
]

base_assets_df["symbol_cleaned"] = base_assets

if __name__ == "__main__":

    headers = {
        "Accept": "application/json",
        "X-Api-Key": KAIKO_API_KEY,
    }

    # with gzip.open(KAIKO_SLIPPAGE_PATH, "wt") as f:

    # for base_asset in BASE_ASSET_LIST:
    # print(base_asset)
    base_asset = "btc"
    params = {
        "start_time": "2021-01-01T00:00:00.000Z",
        # "page_size": 1000,
        "interval": "1h",
        "sort": "asc",
    }
    result_dict = {}
    for base_asset in base_assets:
        results = []
        next_url = f"https://us.market-api.kaiko.io/v2/data/trades.v1/exchanges/bnce/spot/{base_asset.lower()}-usdt/aggregations/count_ohlcv_vwap"
        while True:
            response = requests.get(
                url=next_url,
                headers=headers,
                params=params,
                timeout=100,
            )

            result = response.json()
            result_data = result["data"]
            if result_data:
                results.extend(result_data)
                next_url = result["next_url"]
            else:
                result_dict[base_asset] = results
                break

    # save result_dict to a file
    with open(KAIKO_PRICE_PATH, "w") as f:
        json.dump(result_dict, f)
