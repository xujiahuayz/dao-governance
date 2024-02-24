import gzip
import json

import pandas as pd
import requests

from governenv.settings import KAIKO_API_KEY

BASE_ASSET_LIST = ["aave", "bal"]

headers = {
    "Accept": "application/json",
    "X-Api-Key": KAIKO_API_KEY,
}

# with gzip.open(KAIKO_SLIPPAGE_PATH, "wt") as f:

# for base_asset in BASE_ASSET_LIST:
# print(base_asset)
base_asset = "aave"
params = {
    "start_time": "2020-01-01T00:00:00.000Z",
    "page_size": 1000,
    "interval": "1m",
    "sort": "asc",
}
response = requests.get(
    url=f"https://eu.market-api.kaiko.io/v2/data/trades.v1/spot_direct_exchange_rate/{base_asset}/usd",
    headers=headers,
    params=params,
    timeout=100,
)
# if response.status_code != 200:
#     print(response.status_code)
#     print(response.text)
#     continue
# print(response.url)
result = response.json()
# f.write(json.dumps(result) + "\n")
