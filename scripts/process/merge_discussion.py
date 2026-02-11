"""Script to merge discussion data"""

from ast import literal_eval
from collections import defaultdict
import json

import numpy as np
import pandas as pd
from bs4 import BeautifulSoup

from governenv.constants import DATA_DIR, PROCESSED_DATA_DIR
from governenv.utils import standardized_hhi


def build_discussion_content(
    d: dict,
) -> tuple[list[str], dict[str, float]]:
    """Function to build discussion content for proposals."""

    ds = d["post_stream"]["posts"]
    title = d["title"]

    discussion_contents = []
    discussion_dict = defaultdict(list)

    for discussion in ds:

        # Initial roles
        moderator = False
        admin = False
        staff = False

        # Parse the discussion str
        discussion_str = BeautifulSoup(discussion["cooked"], "html.parser").get_text()

        # Check title
        if discussion["post_number"] == 1:
            title_str = f"{title}\n\n"
        else:
            title_str = ""
            discussion_dict[discussion["username"]].append(discussion_str)

        # Check reply
        if discussion["reply_to_post_number"] is None:
            reply_str = ""
        else:
            reply_str = f" (reply to {discussion['reply_to_post_number']})"

        # Check roles
        if discussion["moderator"]:
            moderator = True
        if discussion["admin"]:
            admin = True
        if discussion["staff"]:
            staff = True

        if moderator | admin | staff:
            role = "["
            if moderator:
                role += "moderator"
            if admin:
                if len(role) > 1:
                    role += ", "
                role += "admin"
            if staff:
                if len(role) > 1:
                    role += ", "
                role += "staff"
            role += "]"
            user_str = f"{discussion['username']} {role}"
        else:
            user_str = discussion["username"]

        formatted = f"{discussion['post_number']}. {user_str}{reply_str}: \
{title_str}{discussion_str}"
        discussion_contents.append(formatted)

    # convert defaultdict to normal dict
    discussion_dict = dict(discussion_dict)

    # discussion statistics
    discussion_statistics_dict = {
        "reply_number": np.log(1 + d["reply_count"]),
        "view_number": np.log(1 + d["views"]),
        "like_number": np.log(1 + d["like_count"]),
        "post_number": np.log(1 + sum(len(v) for k, v in discussion_dict.items())),
        "discussion_created": d["created_at"],
        "hhi_post_number": standardized_hhi(
            [len(v) for k, v in discussion_dict.items()]
        ),
        "hhi_word_count": standardized_hhi(
            [sum(len(post.split()) for post in v) for k, v in discussion_dict.items()]
        ),
    }

    # split by median time (if there are any non-OP posts)
    discussion_wo_post = discussion_contents[1:]
    if len(discussion_wo_post) < 2:
        before_discussions = []
        after_discussions = []
    else:
        cut = len(discussion_wo_post) // 2
        before_discussions = discussion_wo_post[:cut]
        after_discussions = discussion_wo_post[cut:]

    return (
        discussion_contents,
        discussion_statistics_dict,
        before_discussions,
        after_discussions,
    )


# Load proposals data with discussion
df_proposals = pd.read_csv(PROCESSED_DATA_DIR / "proposals_discussion.csv")


for space in df_proposals["space"].unique():
    df_space = df_proposals.loc[df_proposals["space"] == space].copy()
    discussions = []
    for idx, row in df_space.iterrows():
        link = row["discussion"]
        discussion_id = row["discussion_id"]
        file_path = DATA_DIR / "discussion" / space / f"{discussion_id}.json"

        # Check if discussion file exists
        if not file_path.exists():
            continue

        with open(file_path, "r", encoding="utf-8") as f:
            discussion_data = json.load(f)

        # Check if discussion data is valid
        if "post_stream" not in discussion_data:
            continue

        (
            post_discussions,
            discussion_statistics,
            before_discussions,
            after_discussions,
        ) = build_discussion_content(discussion_data)

        # attach to dataframe
        df_proposals.loc[df_proposals["discussion_id"] == discussion_id, "post"] = str(
            post_discussions[0]
        )
        df_proposals.loc[
            df_proposals["discussion_id"] == discussion_id, "post_discussions"
        ] = str(post_discussions[1:])
        df_proposals.loc[
            df_proposals["discussion_id"] == discussion_id, "before_discussions"
        ] = str(before_discussions)
        df_proposals.loc[
            df_proposals["discussion_id"] == discussion_id, "after_discussions"
        ] = str(after_discussions)
        for key, value in discussion_statistics.items():
            df_proposals.loc[df_proposals["discussion_id"] == discussion_id, key] = (
                value
            )

df_proposals.dropna(subset=["post"], inplace=True)
for col in ["post_discussions", "before_discussions", "after_discussions"]:
    df_proposals[col] = df_proposals[col].apply(lambda x: literal_eval(x))
df_proposals = df_proposals.loc[df_proposals["post_discussions"].map(len) > 0]
