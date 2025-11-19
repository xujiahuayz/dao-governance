"""Script to merge topic classification results."""

import json

import pandas as pd

from governenv.constants import PROCESSED_DATA_DIR, TOPICS

df_proposals = pd.read_csv(PROCESSED_DATA_DIR / "proposals_with_sc_blocks.csv")

df_proposals_topics = []
for _, row in df_proposals.iterrows():
    fid = row["id"]
    proposal_topics = {"id": fid}
    for topic in TOPICS:
        topic_file = f"{PROCESSED_DATA_DIR}/topic/{topic.replace(' ', '_')}/{fid}.json"
        with open(topic_file, "r", encoding="utf-8") as fin:
            res = json.load(fin)
        proposal_topics[topic.replace(" ", "_")] = int(res["result"])
    df_proposals_topics.append(proposal_topics)

df_proposals_topics = pd.DataFrame(df_proposals_topics)
df_proposals_topics.to_csv(PROCESSED_DATA_DIR / "proposals_topic.csv", index=False)
