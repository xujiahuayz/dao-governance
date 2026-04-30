"""Script to process before and after discussion data"""

from collections import defaultdict
import json

import pandas as pd
import numpy as np

from scripts.process.nlp_discussion import df_proposals
from governenv.constants import PROCESSED_DATA_DIR, CRITERIA


def parse_string(s: str) -> tuple[str, str, str]:
    """Function to parse the custom_id string into proposal_id, criterion, and type."""
    hash_part, rest = s.split("_", 1)  # split first underscore
    criterion, type_part = rest.rsplit("_", 1)  # split last underscore
    return hash_part, criterion, type_part


gpt_res = defaultdict(lambda: defaultdict(dict))

with open(
    PROCESSED_DATA_DIR / "discussion" / "response" / "before_after_discussion.jsonl",
    "r",
    encoding="utf-8",
) as f:
    batch_responses = [json.loads(line) for line in f.readlines()]

for response in batch_responses:
    proposal_id_criterion = response["custom_id"]
    proposal_id, criterion, typ = parse_string(proposal_id_criterion)
    res = response["response"]["body"]["choices"][0]["logprobs"]["content"][3]["token"]
    logprob = response["response"]["body"]["choices"][0]["logprobs"]["content"][3][
        "logprob"
    ]
    prob = np.exp(logprob)
    gpt_res[proposal_id][criterion][typ] = prob if res == "true" else 1 - prob


df_proposals_char = []
for idx, row in df_proposals.iterrows():
    row_char = row.copy()
    proposal_id = row["id"]
    for criterion in CRITERIA:
        for typ in ["before", "after", "full"]:
            criterion = criterion.lower().replace(" ", "_")
            discussion_data = gpt_res[str(proposal_id)]
            if criterion in discussion_data and typ in discussion_data[criterion]:
                row_char[f"{criterion}_{typ}"] = discussion_data[criterion][typ]
            else:
                row_char[f"{criterion}_{typ}"] = np.nan

    df_proposals_char.append(row_char)

df_proposals = pd.DataFrame(df_proposals_char)
df_proposals.dropna(inplace=True)

SPLIT_VARS = ["post_sentiment", "post_complexity", "post_informativeness"]

for var in SPLIT_VARS:
    median_val = df_proposals[var].median()
    df_proposals[f"{var}_high"] = df_proposals[var] > median_val

df_proposals.drop(
    columns=[
        "body",
        "discussion",
        "post_informativeness",
        "post_sentiment",
        "post_complexity",
        "post",
        "post_discussions",
        "before_discussions",
        "after_discussions",
    ],
    inplace=True,
)

df_proposals.to_csv(
    PROCESSED_DATA_DIR / "proposals_before_after_discussion.csv", index=False
)

# describe criterion based on the split variables
for var in SPLIT_VARS:
    print(f"Criterion scores for {var} high vs low:")
    print(
        df_proposals.groupby(f"{var}_high")[
            [f"{criterion.lower().replace(' ', '_')}_before" for criterion in CRITERIA]
            + [f"{criterion.lower().replace(' ', '_')}_after" for criterion in CRITERIA]
            + [f"{criterion.lower().replace(' ', '_')}_full" for criterion in CRITERIA]
        ].mean()
    )
