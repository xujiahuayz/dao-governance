"""Script to build discussion data"""

from collections import defaultdict
import json

import pandas as pd
import numpy as np

from scripts.process.nlp_discussion import df_proposals
from governenv.constants import PROCESSED_DATA_DIR, CRITERIA


gpt_res = defaultdict(dict)

with open(
    PROCESSED_DATA_DIR / "discussion" / "response" / "discussion.jsonl",
    "r",
    encoding="utf-8",
) as f:
    batch_responses = [json.loads(line) for line in f.readlines()]

for response in batch_responses:
    proposal_id_criterion = response["custom_id"]
    proposal_id, criterion = proposal_id_criterion.split("_", 1)
    res = response["response"]["body"]["choices"][0]["logprobs"]["content"][3]["token"]
    logprob = response["response"]["body"]["choices"][0]["logprobs"]["content"][3][
        "logprob"
    ]
    prob = np.exp(logprob)
    gpt_res[proposal_id][criterion] = prob if res == "true" else 1 - prob


df_proposals_char = []
for idx, row in df_proposals.iterrows():
    row_char = row.copy()
    proposal_id = row["id"]
    for criterion in CRITERIA:
        criterion = criterion.lower().replace(" ", "_")
        discussion_data = gpt_res[str(proposal_id)]
        row_char[criterion] = discussion_data[criterion]

    df_proposals_char.append(row_char)

df_proposals = pd.DataFrame(df_proposals_char)

# min max standardize the criteria scores
for criterion in CRITERIA:

    df_proposals.rename(
        columns={criterion: criterion.lower().replace(" ", "_")}, inplace=True
    )
    criterion = criterion.lower().replace(" ", "_")
    min_val = df_proposals[criterion].min()
    max_val = df_proposals[criterion].max()
    df_proposals[criterion] = (df_proposals[criterion] - min_val) / (max_val - min_val)
    # df_proposals["criterion"] = df_proposals[criterion].apply(
    #     lambda x: x if x >= 0.5 else 0
    # )


df_proposals.to_csv(PROCESSED_DATA_DIR / "proposals_discussion_char.csv", index=False)
