"""Script to label centralized exchange (CEX)"""

import json

import pandas as pd

from tqdm import tqdm

from governenv.constants import DATA_DIR, PROCESSED_DATA_DIR
from governenv.llm import ChatGPT

CEX_TRAFFIC_MAPPING = {
    "btcturk": "btcTurk kripto",
    "gate.io": "gate",
    "crypto.com exchange": "crypto.comexchange",
    "xt": "xt.com",
}

CEX_PROMPT = (
    'Given the centralized exchange named "{cex}", '
    "determine whether most of its users are from China. "
    "Your output should follow this format: "
    '{{"result": <true/false>}}'
)

JSON_SCHEMA = {
    "name": "wallet",
    "schema": {
        "type": "object",
        "properties": {
            "result": {
                "type": "boolean",
            },
        },
        "required": ["result"],
        "additionalProperties": False,
    },
    "strict": True,
}

gpt = ChatGPT(model="gpt-4o")

cex = pd.read_csv(f"{DATA_DIR}/cex.csv")
cex["exchange"] = cex["exchange"].str.lower()
cex["exchange"] = cex["exchange"].replace(CEX_TRAFFIC_MAPPING)
cex = cex.loc[cex["network"] == "ETH"]

cex_china = {}

for exchange in tqdm(cex["exchange"].unique()):
    response = gpt(
        CEX_PROMPT.format(cex=exchange),
        json_schema=JSON_SCHEMA,
    )
    cex_china[exchange] = json.loads(response)["result"]

with open(
    PROCESSED_DATA_DIR / "cex_china.json",
    "w",
    encoding="utf-8",
) as f:
    json.dump(cex_china, f, indent=4)
