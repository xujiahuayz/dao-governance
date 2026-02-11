"""Script to label country"""

import json

from tqdm import tqdm

from governenv.constants import PROCESSED_DATA_DIR
from governenv.llm import ChatGPT


COUNTRY_PROMPT = (
    'Please classify the country "{country}" '
    "into one of the ISO 3166-1 alpha-3 codes. "
    "If the country is not recognized, respond with UNK. "
    "Your output should follow this format: "
    '{{"result": "<ISO>"}}.'
)

JSON_SCHEMA = {
    "name": "wallet",
    "schema": {
        "type": "object",
        "properties": {
            "result": {
                "type": "string",
            },
        },
        "required": ["result"],
        "additionalProperties": False,
    },
    "strict": True,
}

gpt = ChatGPT(model="gpt-4o")


with open(PROCESSED_DATA_DIR / "anchor_country.json", "r", encoding="utf-8") as f:
    anchor_country = json.load(f)

anchor_country_iso = {}
for country in tqdm(anchor_country):
    response = gpt(
        COUNTRY_PROMPT.format(country=country),
        json_schema=JSON_SCHEMA,
    )
    anchor_country_iso[country] = json.loads(response)["result"]

with open(
    PROCESSED_DATA_DIR / "anchor_country_iso.json",
    "w",
    encoding="utf-8",
) as f:
    json.dump(anchor_country_iso, f, indent=4)
