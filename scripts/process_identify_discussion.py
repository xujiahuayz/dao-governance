"""Script to check if a discussion is a forum discussion."""

import glob
import json
import os

from governenv.constants import DATA_DIR, PROCESSED_DATA_DIR
from governenv.llm import build_batch, ChatGPT
from governenv.prompts import IDF_INSTRUCT, IDF_JSON_SCHEMA, IDF_PROMPT

BATCH_NAME = "identify_forum_discussion_batches"
chat_gpt = ChatGPT()

html_files = glob.glob(f"{DATA_DIR}/discussion/*.html")
html_id = [fp.split("/")[-1].replace(".html", "") for fp in html_files]
txt_files = glob.glob(f"{DATA_DIR}/discussion/*.txt")
txt_id = [fp.split("/")[-1].replace(".txt", "") for fp in txt_files]

discussion_dict = {}

for fid in html_id:
    with open(f"{DATA_DIR}/discussion/{fid}.html", "r", encoding="utf-8") as f:
        content = f.read()
        discussion_dict[fid] = content

for fid in txt_id:
    with open(f"{DATA_DIR}/discussion/{fid}.txt", "r", encoding="utf-8") as f:
        content = f.read()
        discussion_dict[fid] = content

for save_path in ["batch", "batch_output"]:
    os.makedirs(f"{PROCESSED_DATA_DIR}/{save_path}", exist_ok=True)

with open(
    f"{PROCESSED_DATA_DIR}/batch/identify_forum_discussion_batches.jsonl",
    "w",
    encoding="utf-8",
) as f:
    for fid, content in discussion_dict.items():
        user_msg = IDF_PROMPT.format(content=content)
        batch = build_batch(
            custom_id=fid,
            user_msg=user_msg,
            system_instruction=IDF_INSTRUCT,
            json_schema=IDF_JSON_SCHEMA,
            model="gpt-4.1",
            temperature=0,
        )
        f.write(json.dumps(batch) + "\n")

batch_id = chat_gpt.send_batch(f"{PROCESSED_DATA_DIR}/batch/{BATCH_NAME}.jsonl")
result = chat_gpt.retrieve_batch(batch_id)
with open(f"{PROCESSED_DATA_DIR}/batch_output/{BATCH_NAME}.jsonl", "wb") as file:
    file.write(result)
