"""Script to use GPT to classify proposal topics."""

import json
import os

from tqdm import tqdm
import numpy as np

from governenv.constants import PROCESSED_DATA_DIR, CRITERIA
from governenv.llm import ChatGPT
from governenv.prompts import DISCUSSION_INSTRUCT, DISCUSSION_PROMPT, JSON_SCHEMA
from scripts.merge_discussion import df_proposals

chat_gpt = ChatGPT(model="gpt-4o")

os.makedirs(PROCESSED_DATA_DIR / "discussion_sup", exist_ok=True)

for _, row in tqdm(df_proposals.iterrows(), total=len(df_proposals)):
    proposal_id = row["id"]
    post = row["post"]
    discussion = row["post_discussions"]

    criterion_results = {}
    try:
        for criterion in CRITERIA:
            res, probs = chat_gpt(
                message=DISCUSSION_PROMPT.format(
                    criterion=criterion, post=post, discussion="\n\n".join(discussion)
                ),
                instruction=DISCUSSION_INSTRUCT,
                json_schema=JSON_SCHEMA,
                temperature=0,
                logprobs=True,
                top_logprobs=2,
            )
            res = json.loads(res)
            criterion_results[criterion] = {
                "result": res["result"],
                "probs": (
                    np.exp(probs[3].logprob)
                    if res["result"]
                    else 1 - np.exp(probs[3].logprob)
                ),
            }
    except Exception as e:
        print(f"Error processing proposal {proposal_id}: {e}")
        continue

    with open(
        PROCESSED_DATA_DIR / "discussion_sup" / f"{proposal_id}.json",
        "w",
        encoding="utf-8",
    ) as fout:
        json.dump(criterion_results, fout)
