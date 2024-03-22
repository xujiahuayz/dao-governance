import json

from governenv.constants import KAIKO_PRICE_PATH
from scripts.fetch_kaiko_price import base_assets_df

# read json file
with open(KAIKO_PRICE_PATH, "r") as f:
    data = json.load(f)

data["UNI"]
