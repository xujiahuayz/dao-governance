"""Script to merge Coingecko coin smart contract data."""

import gzip
import os
import json
import pandas as pd
from tqdm import tqdm

from governenv.constants import DATA_DIR, PROCESSED_DATA_DIR


coingecko_coins = pd.read_csv(DATA_DIR / "coingecko_coins.csv")


id_sc = {}
for idx, row in tqdm(coingecko_coins.iterrows(), total=coingecko_coins.shape[0]):
    gecko_id = row["id"]
    gecko_name = row["name"]
    gecko_symbol = row["symbol"]

    if os.path.exists(f"{DATA_DIR}/coingecko/coins/{gecko_id}.json"):
        with open(
            f"{DATA_DIR}/coingecko/coins/{gecko_id}.json",
            "r",
            encoding="utf-8",
        ) as f:
            data = json.load(f)
        if "detail_platforms" in data and data["detail_platforms"]:
            id_sc[gecko_id] = data["detail_platforms"]

with gzip.open(
    PROCESSED_DATA_DIR / "coingecko_id_smart_contract.json.gz",
    "wt",
    encoding="utf-8",
) as f:
    json.dump(id_sc, f, indent=4)
