"""Script to process votes data"""

from ast import literal_eval
import re
import glob
import json

from collections import defaultdict
import pandas as pd
import numpy as np
from tqdm import tqdm

from governenv.constants import DATA_DIR, PROCESSED_DATA_DIR, NO, ABSTAIN, YES
from governenv.utils import calc_hhi, match_keywords

from scripts.process_event_study import (
    df_proposals_adj,
)

URL_RE = re.compile(r"https?://\S+|www\.\S+")
CODE_RE = re.compile(r"`{1,3}.*?`{1,3}", re.DOTALL)
MULTISPACE_RE = re.compile(r"\s+")


def close_call_index(scores: list[float]) -> float:
    """Calculate the close call index."""

    if len(scores) == 0:
        return np.nan

    max_scores = max(scores)
    sum_scores = sum(scores)
    len_scores = len(scores)

    if not scores or len(scores) < 2 or len_scores == 0 or sum_scores == 0:
        return np.nan

    return (max_scores / sum_scores) - (1 / len_scores)


if __name__ == "__main__":

    # # load the proposal data with block and smart contract info
    # df_proposals_adj = pd.read_csv(
    #     PROCESSED_DATA_DIR / "proposals_adjusted_with_sc_block.csv"
    # )
    # df_proposals_adj["scores"] = df_proposals_adj["scores"].apply(literal_eval)

    # load the vote data for all proposals
    votes_files = glob.glob(str(DATA_DIR / "snapshot" / "votes" / "*.jsonl"))
    df_votes = []
    for file in tqdm(votes_files):
        proposal_id = file.split("/")[-1].replace(".jsonl", "")
        with open(
            file,
            "r",
            encoding="utf-8",
        ) as f:
            df_vote = defaultdict(list)
            for line in f:
                vote = json.loads(line)
                for col in [
                    "id",
                    "ipfs",
                    "voter",
                    "created",
                    "metadata",
                    "reason",
                    "app",
                    "vp",
                    "vp_by_strategy",
                    "vp_state",
                ]:
                    df_vote[col].append(vote[col])
                if isinstance(vote["choice"], dict):
                    df_vote["type"].append("dict")
                    df_vote["choice"].append(vote["choice"])
                elif isinstance(vote["choice"], list):
                    df_vote["type"].append("list")
                    df_vote["choice"].append(vote["choice"])
                elif isinstance(vote["choice"], str):
                    df_vote["type"].append("string")
                    df_vote["choice"].append(vote["choice"])
                else:
                    df_vote["type"].append("single")
                    df_vote["choice"].append(int(vote["choice"]))
                df_vote["proposal_id"].append(vote["proposal"]["id"])
            if len(df_vote) == 0:
                continue

        df_vote = pd.DataFrame(df_vote)
        df_votes.append(df_vote)
    df_votes = pd.concat(df_votes, ignore_index=True)
    df_votes.to_csv(PROCESSED_DATA_DIR / "votes.csv", index=False)

    # calculate the voter-level characteristics
    df_vote_c = defaultdict(list)
    for proposal_id, group in tqdm(
        df_votes.groupby("proposal_id"), desc="Processing proposals"
    ):
        df_vote_c["id"].append(proposal_id)
        group = group.sort_values(by="vp", ascending=False)

        # Half Voting Weight Ratio
        vp = group["vp"].tolist()
        half_vp = sum(vp) / 2
        vp_cumsum = np.sort(vp)[::-1].cumsum()
        k = int(np.searchsorted(vp_cumsum, half_vp)) + 1
        half_vp_ratio = k / len(vp) if len(vp) > 0 else np.nan
        df_vote_c["half_vp_ratio"].append(half_vp_ratio)

        # Choice type
        if len(group["type"].unique()) != 1:
            df_vote_c["vn_hhi"].append(np.nan)
            continue

        match group["type"].unique()[0]:
            case "dict":
                group_type = []
                for idx, row in group.iterrows():
                    if len(row["choice"]) == 0:
                        continue
                    all_weights = sum(row["choice"].values())
                    for choice, weight in row["choice"].items():
                        row_copy = row.copy()
                        row_copy["choice"] = choice
                        row_copy["vp"] = weight / all_weights * row_copy["vp"]
                        group_type.append(row_copy)
                group = pd.DataFrame(group_type)
            case "list":
                group_type = []
                for idx, row in group.iterrows():
                    if len(row["choice"]) == 0:
                        continue
                    row["choice"] = row["choice"][0]
                    group_type.append(row)
                group = pd.DataFrame(group_type)

        # Voting Number HHI
        voting_number = group.groupby("choice")["voter"].count().to_list()
        vn_hhi = calc_hhi(voting_number)
        df_vote_c["vn_hhi"].append(vn_hhi)

    # Merge the voter-level characteristics to proposal data
    df_proposals_adj = df_proposals_adj.merge(
        pd.DataFrame(df_vote_c), on="id", how="left"
    )

    # Calculate the voting score HHI
    df_proposals_adj["vs_hhi"] = df_proposals_adj["scores"].apply(calc_hhi)

    # Calculate the close call index
    df_proposals_adj["cci"] = df_proposals_adj["scores"].apply(close_call_index)

    # # Vote characteristics
    # df_proposals_adj["votes"] = np.log(df_proposals_adj["votes"] + 1)
    # df_proposals_adj["n_choices"] = df_proposals_adj["choices"].apply(len)
    # df_proposals_adj["agree"] = df_proposals_adj["scores"].apply(calc_hhi)
    # df_proposals_adj["duration"] = (
    #     df_proposals_adj["end"] - df_proposals_adj["start"]
    # ).dt.days
    # df_proposals_adj["quadratic"] = (df_proposals_adj["type"] == "quadratic").astype(
    #     int
    # )
    # df_proposals_adj["ranked_choice"] = (
    #     df_proposals_adj["type"] == "ranked-choice"
    # ).astype(int)

    # df_proposals_adj["choices"] = df_proposals_adj["choices"].apply(
    #     lambda choices: [choice.lower() for choice in choices]
    # )

    # Convert the scores to percentage
    df_proposals_adj["scores_pct"] = df_proposals_adj.apply(
        lambda row: (
            [score / sum(row["scores"]) for score in row["scores"]]
            if sum(row["scores"]) > 0
            else [0 for _ in row["scores"]]
        ),
        axis=1,
    )
    df_proposals_adj["choices_scores_pct"] = df_proposals_adj.apply(
        lambda row: sorted(
            list(zip(row["choices"], row["scores_pct"])),
            key=lambda x: x[1],
            reverse=True,
        ),
        axis=1,
    )

    df_proposals_adj["binary"] = df_proposals_adj["choices_scores_pct"].apply(
        lambda choices: any(
            match_keywords(choice_text, NO) for choice_text, _ in (choices or [])
        )
    )

    def share_for_keywords(row: pd.Series, keywords: set) -> float:
        """Sum of vote shares for options that match the keyword set."""

        if not row["binary"]:
            return np.nan

        return sum(
            p
            for ch, p in zip(row["choices"], row["scores_pct"])
            if match_keywords(ch, keywords)
        )

    df_proposals_adj["reject"] = df_proposals_adj["choices_scores_pct"].apply(
        lambda choices: (
            match_keywords(choices[0][0], NO | ABSTAIN)
            if choices and len(choices) > 0
            else False
        )
    )
    for var in ["reject", "binary"]:
        df_proposals_adj[var] = df_proposals_adj[var].astype(int)

    # 1) Per-proposal YES share and REJECT share
    df_proposals_adj["reject_pct"] = df_proposals_adj.apply(
        lambda r: share_for_keywords(r, NO | ABSTAIN), axis=1
    )

    df_proposals_adj.to_csv(
        PROCESSED_DATA_DIR / "proposals_adjusted_votes.csv", index=False
    )
