"""Script to use GPT to classify proposal topics."""

import json
import os

import pandas as pd
from tqdm import tqdm

from governenv.constants import PROCESSED_DATA_DIR, TOPICS
from governenv.llm import ChatGPT
from governenv.prompts import TOPIC_PROMPT, TOPIC_INSTRUCT, JSON_SCHEMA

chat_gpt = ChatGPT(model="gpt-4o")


df_proposals = pd.read_csv(PROCESSED_DATA_DIR / "proposals_with_sc_blocks.csv")
df_proposals["title_body"] = df_proposals["title"] + "\n" + df_proposals["body"]

# get the id title_dody dict
proposal_dict = {}
for _, row in df_proposals.iterrows():
    proposal_dict[row["id"]] = row["title_body"]

for topic in TOPICS:
    os.makedirs(f"{PROCESSED_DATA_DIR}/topic/{topic.replace(" ", "_")}", exist_ok=True)
    for fid, proposal in tqdm(proposal_dict.items()):
        if os.path.exists(
            f"{PROCESSED_DATA_DIR}/topic/{topic.replace(' ', '_')}/{fid}.json"
        ):
            continue

        res = chat_gpt(
            message=TOPIC_PROMPT.format(topic=topic, proposal=proposal),
            instruction=TOPIC_INSTRUCT,
            json_schema=JSON_SCHEMA,
            temperature=0,
        )
        res = json.loads(res)
        with open(
            f"{PROCESSED_DATA_DIR}/topic/{topic.replace(" ", "_")}/{fid}.json",
            "w",
            encoding="utf-8",
        ) as fout:
            json.dump(res, fout)
