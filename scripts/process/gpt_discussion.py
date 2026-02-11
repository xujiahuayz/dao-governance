"""Script to use GPT to classify proposal topics."""

import json
import os

from tqdm import tqdm

from governenv.constants import PROCESSED_DATA_DIR, CRITERIA
from governenv.llm import ChatGPT, build_batch
from governenv.prompts import DISCUSSION_INSTRUCT, DISCUSSION_PROMPT, JSON_SCHEMA
from scripts.process.merge_discussion import df_proposals

BATCH_PATH = PROCESSED_DATA_DIR / "discussion" / "batch" / "discussion.jsonl"
chat_gpt = ChatGPT(model="gpt-4o")

for path in ["discussion", "discussion/batch", "discussion/response"]:
    os.makedirs(PROCESSED_DATA_DIR / path, exist_ok=True)


# # Full discussion
# batch = []
# for _, row in tqdm(df_proposals.iterrows(), total=len(df_proposals)):
#     proposal_id = row["id"]
#     post = row["post"]
#     discussion = row["post_discussions"]

#     for criterion in CRITERIA:
#         criterion_lower = criterion.lower().replace(" ", "_")
#         batch.append(
#             build_batch(
#                 custom_idx=f"{proposal_id}_{criterion_lower}",
#                 user_msg=DISCUSSION_PROMPT.format(
#                     criterion=criterion,
#                     post=post,
#                     discussion="\n\n".join(discussion),
#                 ),
#                 system_instruction=DISCUSSION_INSTRUCT,
#                 json_schema=JSON_SCHEMA,
#                 model="gpt-4o",
#             )
#         )

# # save batch requests
# with open(BATCH_PATH, "w", encoding="utf-8") as f:
#     for item in batch:
#         f.write(json.dumps(item) + "\n")

# # send batch requests
# batch_id = chat_gpt.send_batch(BATCH_PATH)

# # retrieve responses
# responses = chat_gpt.retrieve_batch(batch_id)

# # save responses
# with open(
#     PROCESSED_DATA_DIR / "discussion" / "response" / "discussion.json",
#     "w",
#     encoding="utf-8",
# ) as f:
#     json.dump(responses, f, indent=4)

# before and after discussion
batch = []

for _, row in tqdm(df_proposals.iterrows(), total=len(df_proposals)):
    proposal_id = row["id"]
    post = row["post"]

    for criterion in CRITERIA:
        for typ in ["full", "before", "after"]:
            discussions = (
                row[f"{typ}_discussions"] if typ != "full" else row["post_discussions"]
            )

            if len(discussions) == 0:
                continue

            criterion_lower = criterion.lower().replace(" ", "_")
            batch.append(
                build_batch(
                    custom_idx=f"{proposal_id}_{criterion_lower}_{typ}",
                    user_msg=DISCUSSION_PROMPT.format(
                        criterion=criterion,
                        post=post,
                        discussion="\n\n".join(discussions),
                    ),
                    system_instruction=DISCUSSION_INSTRUCT,
                    json_schema=JSON_SCHEMA,
                    model="gpt-4o",
                )
            )

# save batch requests
with open(
    PROCESSED_DATA_DIR / "discussion" / "batch" / "before_after_discussion.jsonl",
    "w",
    encoding="utf-8",
) as f:
    for item in batch:
        f.write(json.dumps(item) + "\n")

# send batch requests
batch_id = chat_gpt.send_batch(
    PROCESSED_DATA_DIR / "discussion" / "batch" / "before_after_discussion.jsonl"
)

# retrieve responses
responses = chat_gpt.retrieve_batch(batch_id)

# save responses
with open(
    PROCESSED_DATA_DIR / "discussion" / "response" / "before_after_discussion.json",
    "w",
    encoding="utf-8",
) as f:
    json.dump(responses, f, indent=4)
