"""Script to process discussion data for regression analysis."""

import glob
import math
import os
import json

from tqdm import tqdm
from bs4 import BeautifulSoup

from governenv.constants import PROCESSED_DATA_DIR, DATA_DIR
from governenv.llm import ChatGPT
from governenv.prompts import EVAL_INSTRUCT, EVAL_PROMPT

chat_gpt = ChatGPT()

with open(
    f"{PROCESSED_DATA_DIR}/batch_output/identify_forum_discussion_batches.jsonl",
    "r",
    encoding="utf-8",
) as f:
    lines = f.readlines()

discussions = [json.loads(line) for line in lines]
forum_discussions = [
    _["custom_id"]
    for _ in discussions
    if json.loads(_["response"]["body"]["choices"][0]["message"]["content"])[
        "is_forum_discussion"
    ]
]

os.makedirs(f"{PROCESSED_DATA_DIR}/sentiment", exist_ok=True)
finished_files = glob.glob(str(PROCESSED_DATA_DIR / "sentiment" / "*.json"))
finished_ids = [file.split("/")[-1].replace(".json", "") for file in finished_files]

for fid in tqdm(forum_discussions):
    if fid in finished_ids:
        continue
    try:
        if os.path.exists(f"{DATA_DIR}/discussion/{fid}.html"):
            with open(f"{DATA_DIR}/discussion/{fid}.html", "r", encoding="utf-8") as f:
                content = f.read()
            soup = BeautifulSoup(content, "html.parser")
            # Remove script and style elements
            for script_or_style in soup(["script", "style", "noscript"]):
                script_or_style.decompose()
            content = str(soup)
        else:
            with open(f"{DATA_DIR}/discussion/{fid}.txt", "r", encoding="utf-8") as f:
                content = f.read()

        eval_dict = {}
        eval_res = chat_gpt(
            message=EVAL_PROMPT.format(content=content),
            instruction=EVAL_INSTRUCT,
            logprobs=True,
            top_logprobs=2,
        )
        eval, prob = eval_res
        eval_prob = [
            _ for _ in prob if any(binary in _.token for binary in ["Yes", "No"])
        ]
        yes_prob = [
            math.exp(_.logprob) if "Yes" in _.token else 1 - math.exp(_.logprob)
            for _ in eval_prob
        ]
        class_prob = {
            "Support": yes_prob[0],
            "Professionalism": yes_prob[1],
            "Objectiveness": yes_prob[2],
            "Unanimity": yes_prob[3],
        }
        # save the class_prob
        with open(
            f"{PROCESSED_DATA_DIR}/sentiment/{fid}.json",
            "w",
            encoding="utf-8",
        ) as f:
            json.dump(class_prob, f, indent=4)

    except Exception as e:
        print(f"Error processing discussion {fid}: {e}")
        continue
