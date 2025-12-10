"""Script to build discussion data"""

import json

import pandas as pd

from scripts.merge_discussion import df_proposals
from governenv.constants import PROCESSED_DATA_DIR, CRITERIA

df_proposals_char = []
for idx, row in df_proposals.iterrows():
    row_char = row.copy()
    proposal_id = row["id"]

    with open(
        PROCESSED_DATA_DIR / "discussion" / f"{proposal_id}.json", "r", encoding="utf-8"
    ) as fin:
        discussion_data = json.load(fin)

    with open(
        PROCESSED_DATA_DIR / "discussion_sup" / f"{proposal_id}.json",
        "r",
        encoding="utf-8",
    ) as fin_sup:
        discussion_sup_data = json.load(fin_sup)

    discussion_data.update(discussion_sup_data)

    for criterion in CRITERIA:
        row_char[criterion] = discussion_data[criterion]["probs"]

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
