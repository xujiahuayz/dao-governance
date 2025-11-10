"""Script to process participant data."""

from copy import deepcopy
from collections import defaultdict
import os
from ast import literal_eval
import json

import pandas as pd
from tqdm import tqdm
import numpy as np

from governenv.constants import PROCESSED_DATA_DIR
from governenv.utils import standardized_hhi


WHALE_THRESHOLD = 0.05
os.makedirs(PROCESSED_DATA_DIR / "holding_pct", exist_ok=True)


def calc_frequency(choices: list) -> defaultdict:
    """Function to calculate choice frequency."""
    frequency = defaultdict(int)
    for c in choices:
        frequency[c] += 1
    return frequency


def calc_vp(choices: list, vps: list) -> defaultdict:
    """Function to calculate choice vp."""
    vp_dict = defaultdict(float)
    for idx, c in enumerate(choices):
        vp_dict[c] += vps[idx]
    return vp_dict


def calc_delegation(
    records: list,
    directions: str,
    groups: str,
    total_holdings: float,
) -> int:
    """Function to calculate delegation counts."""

    direction_str = "delegator" if directions == "from" else "delegatee"
    if groups == "whale":
        filtered_set = set(
            record[direction_str]
            for record in records
            if record[f"{direction_str}_holding"] >= (WHALE_THRESHOLD * total_holdings)
        )
    else:
        filtered_set = set(
            record[direction_str]
            for record in records
            if record[f"{direction_str}_holding"] < (WHALE_THRESHOLD * total_holdings)
        )
    return len(filtered_set)


if __name__ == "__main__":
    # Load the proposal data with smart contract and block info
    df_proposals = pd.read_csv(PROCESSED_DATA_DIR / "proposals_with_sc_blocks.csv")
    # df_proposals = df_proposals.loc[
    #     df_proposals["id"]
    #     == "0x8eb143cdf1608513078270f6c0302e30faa2155cce748e74678bde2ef4091f46"
    # ]
    for col in ["address", "choices", "scores", "scores_by_strategy"]:
        df_proposals[col] = df_proposals[col].apply(literal_eval)

    # Load the vote data
    df_votes = pd.read_csv(PROCESSED_DATA_DIR / "votes.csv")
    df_votes["voter"] = df_votes["voter"].str.lower()

    df_proposals_participation = []
    for _, row in tqdm(df_proposals.iterrows(), total=len(df_proposals)):
        # Initialize proposal participation data
        proposal_participation = deepcopy(row)

        # Load token, block, and price info
        strategies = row["strategies"]
        proposal_id = row["id"]
        space = row["space"]
        creation_block = row["created_ts_block"]
        creation_price = row["created_price"]
        delegation = row["delegation"]
        start_ts = row["start_ts"]
        end_ts = row["end_ts"]
        win_choice = str(
            sorted(
                zip(
                    [str(idx + 1) for idx, _ in enumerate(row["choices"])],
                    row["scores"],
                ),
                key=lambda x: x[1],
                reverse=True,
            )[0][0]
            if row["scores"]
            else None
        )

        # Load the voter data
        df_vote_subset = df_votes[df_votes["proposal_id"] == proposal_id].copy()
        voter_set = set(df_vote_subset["voter"].tolist())

        # Check if all vote types are the same
        if len(df_vote_subset["type"].unique()) == 1:
            match df_vote_subset["type"].unique()[0]:
                case "dict":
                    group_type = []
                    df_vote_subset["choice"] = df_vote_subset["choice"].apply(
                        literal_eval
                    )
                    for _, row_vote in df_vote_subset.iterrows():
                        if len(row_vote["choice"]) == 0:
                            continue
                        all_weights = sum(row_vote["choice"].values())
                        for choice, weight in row_vote["choice"].items():
                            row_copy = row_vote.copy()
                            row_copy["choice"] = choice
                            row_copy["vp"] = weight / all_weights * row_copy["vp"]
                            group_type.append(row_copy)
                    df_vote_subset = pd.DataFrame(group_type)
                case "list":
                    df_vote_subset["choice"] = df_vote_subset["choice"].apply(
                        literal_eval
                    )
                    group_type = []
                    for _, row_vote in df_vote_subset.iterrows():
                        if len(row_vote["choice"]) == 0:
                            continue
                        row_vote["choice"] = row_vote["choice"][0]
                        group_type.append(row_vote)
                    df_vote_subset = pd.DataFrame(group_type)

        # Iterate through each token associated with the proposal
        all_holding_data = []
        for token_address_info in row["address"]:
            token_address = token_address_info["address"]
            # Load the holding data
            with open(
                PROCESSED_DATA_DIR
                / "holding_dep"
                / f"{token_address}"
                / f"{token_address}_{creation_block}.json",
                "r",
                encoding="utf-8",
            ) as f:
                holding_data = json.load(f)

            all_holding_data.append(holding_data)

        # Merge holdings from multiple tokens by summing up holdings for each wallet
        total_holding_data = {}
        for holding_data in all_holding_data:
            for addr, info in holding_data.items():
                if addr not in total_holding_data:
                    total_holding_data[addr] = {
                        "holding": 0,
                        "contract": info["contract"],
                    }
                total_holding_data[addr]["holding"] += info["holding"]
        holder_set = set(total_holding_data.keys())

        # Only keep the voter with holding greater than 0 and not a contract
        wallet_holding_data = {
            k: v["holding"]
            for k, v in total_holding_data.items()
            if (v["holding"] > 0) and (v["contract"] is False)
        }
        total_holding = sum(wallet_holding_data.values())

        # Calculate total number of holders and whales
        total_number_of_holders = len(wallet_holding_data)
        total_whale_dict = {
            k: v
            for k, v in wallet_holding_data.items()
            if v >= (WHALE_THRESHOLD * total_holding)
        }
        total_non_whale_dict = {
            k: v
            for k, v in wallet_holding_data.items()
            if v < (WHALE_THRESHOLD * total_holding)
        }
        total_whale_set = set(total_whale_dict.keys())
        total_non_whale_set = set(total_non_whale_dict.keys())

        # Handle delegation
        delegatee_set = set()
        if delegation == "delegation":
            with open(
                PROCESSED_DATA_DIR / "delegation" / f"delegation_{creation_block}.json",
                "r",
                encoding="utf-8",
            ) as f:
                delegation_data = json.load(f)
            delegator_set = set(delegation_data.keys())

            delegation_records = []
            if holder_set & delegator_set:
                for delegator in holder_set & delegator_set:
                    delegatee = None
                    if "all" in delegation_data[delegator]:
                        delegatee = delegation_data[delegator]["all"]
                    if space in delegation_data[delegator]:
                        delegatee = delegation_data[delegator][space]

                    # If there is a delegatee and the delegator did not vote
                    if delegatee and delegator not in voter_set:
                        delegatee_set.add(delegatee)
                        # Transfer voting power to delegatee
                        if delegatee not in total_holding_data:
                            total_holding_data[delegatee] = {
                                "holding": 0,
                                "contract": False,
                            }
                        total_holding_data[delegatee]["holding"] += total_holding_data[
                            delegator
                        ]["holding"]

                        # Record the delegation
                        delegation_records.append(
                            {
                                "delegator": delegator,
                                "delegatee": delegatee,
                                "delegator_holding": total_holding_data[delegator][
                                    "holding"
                                ],
                                "delegatee_holding": total_holding_data[delegatee][
                                    "holding"
                                ],
                                "delegator_contract": total_holding_data[delegator][
                                    "contract"
                                ],
                            }
                        )

                        # del total_holding_data[delegator]
                        del total_holding_data[delegator]

        voting = {"voters": {}}
        unknown_voters = []
        # iterate through voters
        for _, vote_row in df_vote_subset.iterrows():
            voter = vote_row["voter"]
            if voter in total_holding_data:
                holding = total_holding_data[voter]
                label = (
                    "whales"
                    if holding["holding"] >= (WHALE_THRESHOLD * total_holding)
                    else "non_whales"
                )
                voting["voters"][voter] = {
                    "label": label,
                    "vp": vote_row["vp"],
                    "holding": holding["holding"],
                    "contract": holding["contract"],
                    "choice": vote_row["choice"],
                    "reason": 1 if pd.notna(vote_row["reason"]) else 0,
                    "created": vote_row["created"],
                    "timing": (int(vote_row["created"]) - int(start_ts))
                    / (int(end_ts) - int(start_ts)),
                }
            else:
                unknown_voters.append(
                    {
                        "voter": voter,
                        "vp": vote_row["vp"],
                    }
                )

        # Skip proposals with unknown voters
        if len(unknown_voters) > 0:
            continue

        # Separate whale and non-whale voters
        non_whale_vote = {
            k: v for k, v in voting["voters"].items() if v["label"] == "non_whales"
        }
        non_whale_vote = dict(
            sorted(non_whale_vote.items(), key=lambda item: item[1]["vp"])
        )
        whale_vote = {
            k: v for k, v in voting["voters"].items() if v["label"] == "whales"
        }
        whale_vote = dict(sorted(whale_vote.items(), key=lambda item: item[1]["vp"]))

        first_whale_vote = (
            min([v["created"] for k, v in whale_vote.items()]) if whale_vote else np.nan
        )

        # Calculate standardized HHI for whale and non-whale voters
        whale_freq = calc_frequency([v["choice"] for k, v in whale_vote.items()])
        non_whale_freq = calc_frequency(
            [v["choice"] for k, v in non_whale_vote.items()]
        )
        whale_vp = calc_vp(
            [v["choice"] for k, v in whale_vote.items()],
            [v["vp"] for k, v in whale_vote.items()],
        )
        non_whale_vp = calc_vp(
            [v["choice"] for k, v in non_whale_vote.items()],
            [v["vp"] for k, v in non_whale_vote.items()],
        )

        proposal_participation["whale_vn_hhi"] = (
            standardized_hhi(whale_freq.values())
            if len(df_vote_subset["type"].unique()) == 1
            else np.nan
        )
        proposal_participation["non_whale_vn_hhi"] = (
            standardized_hhi(non_whale_freq.values())
            if len(df_vote_subset["type"].unique()) == 1
            else np.nan
        )
        proposal_participation["whale_vs_hhi"] = (
            standardized_hhi(whale_freq.values())
            if len(df_vote_subset["type"].unique()) == 1
            else np.nan
        )
        proposal_participation["non_whale_vs_hhi"] = (
            standardized_hhi(non_whale_freq.values())
            if len(df_vote_subset["type"].unique()) == 1
            else np.nan
        )

        # Calculate the winrate
        proposal_participation["whale_win_vn"] = (
            int(win_choice == str(max(whale_freq, key=whale_freq.get)))
            if whale_freq and len(df_vote_subset["type"].unique()) and win_choice
            else np.nan
        )
        proposal_participation["whale_win_vp"] = (
            int(win_choice == str(max(whale_vp, key=whale_vp.get)))
            if whale_vp and len(df_vote_subset["type"].unique()) and win_choice
            else np.nan
        )
        proposal_participation["non_whale_win_vn"] = (
            int(win_choice == str(max(non_whale_freq, key=non_whale_freq.get)))
            if non_whale_freq and len(df_vote_subset["type"].unique()) and win_choice
            else np.nan
        )
        proposal_participation["non_whale_win_vp"] = (
            int(win_choice == str(max(non_whale_vp, key=non_whale_vp.get)))
            if non_whale_vp and len(df_vote_subset["type"].unique()) and win_choice
            else np.nan
        )

        # Very few smart contract whales/non-whales vote and delegation
        non_whale_votable_contract_set = set(
            k for k, v in non_whale_vote.items() if v["contract"] is True
        )
        whale_votable_contract_set = set(
            k for k, v in whale_vote.items() if v["contract"] is True
        )

        non_whale_votable_contract_no_delegate = deepcopy(
            non_whale_votable_contract_set
        )
        whale_votable_contract_no_delegate = deepcopy(whale_votable_contract_set)

        if delegation == "delegation":
            non_whale_votable_contract_set = non_whale_votable_contract_set | set(
                _["delegator"]
                for _ in delegation_records
                if _["delegator_contract"] is True
                and _["delegator_holding"] < (WHALE_THRESHOLD * total_holding)
            )
            whale_votable_contract_set = whale_votable_contract_set | set(
                _["delegator"]
                for _ in delegation_records
                if _["delegator_contract"] is True
                and _["delegator_holding"] >= (WHALE_THRESHOLD * total_holding)
            )

        # Delegatee that does not appear in pre-delegation voter list
        whale_delegatee_new_voter = set(
            _
            for _ in delegatee_set
            if _ in total_holding_data
            if total_holding_data[_]["holding"] >= (WHALE_THRESHOLD * total_holding)
        )
        non_whale_delegatee_new_voter = set(
            _
            for _ in delegatee_set
            if _ in total_holding_data
            if total_holding_data[_]["holding"] < (WHALE_THRESHOLD * total_holding)
        )

        # Update the proposal participation data
        holder_num = total_number_of_holders
        whale_num = len(
            total_whale_set | whale_votable_contract_set | whale_delegatee_new_voter
        )
        non_whale_num = len(
            total_non_whale_set
            | non_whale_votable_contract_set
            | non_whale_delegatee_new_voter
        )
        proposal_participation["holder_num"] = holder_num
        proposal_participation["whale_num"] = whale_num
        proposal_participation["non_whale_num"] = non_whale_num
        proposal_participation["whale_vote_num"] = len(whale_vote)
        proposal_participation["non_whale_vote_num"] = len(non_whale_vote)
        proposal_participation["whale_reason_num"] = sum(
            v["reason"] for k, v in whale_vote.items()
        )
        proposal_participation["non_whale_reason_num"] = sum(
            v["reason"] for k, v in non_whale_vote.items()
        )
        proposal_participation["whale_timing_avg"] = (
            np.mean([v["timing"] for k, v in whale_vote.items()])
            if len(whale_vote) > 0
            else np.nan
        )
        proposal_participation["non_whale_timing_avg"] = (
            np.mean([v["timing"] for k, v in non_whale_vote.items()])
            if len(non_whale_vote) > 0
            else np.nan
        )

        # Update the delegation records
        for direction in ["from", "to"]:
            for group in ["whale", "non_whale"]:
                proposal_participation[f"{group}_{direction}_delegation_num"] = (
                    (
                        calc_delegation(
                            delegation_records,
                            direction,
                            group,
                            total_holding,
                        )
                    )
                    if delegation == "delegation"
                    else np.nan
                )

        # Calculate the pre-delegation rates:
        for group in ["whale", "non_whale"]:
            for direction in ["from", "to"]:
                # calculate the from delegation rate
                proposal_participation[f"{group}_{direction}_delegation_rate"] = (
                    proposal_participation[f"{group}_{direction}_delegation_num"]
                    / proposal_participation[f"{group}_num"]
                    if proposal_participation[f"{group}_num"] > 0
                    else np.nan
                )

        # Calculate the turnout and to-delegation rates
        # Only keep the voter with holding greater than 0 and not a contract
        wallet_holding_data = {
            k: v["holding"]
            for k, v in total_holding_data.items()
            if (v["holding"] > 0) and (v["contract"] is False)
        }
        total_holding = sum(wallet_holding_data.values())

        # Calculate total number of holders and whales
        total_number_of_holders = len(wallet_holding_data)
        total_whale_dict = {
            k: v
            for k, v in wallet_holding_data.items()
            if v >= (WHALE_THRESHOLD * total_holding)
        }
        total_non_whale_dict = {
            k: v
            for k, v in wallet_holding_data.items()
            if v < (WHALE_THRESHOLD * total_holding)
        }
        total_whale_set = set(total_whale_dict.keys())
        total_non_whale_set = set(total_non_whale_dict.keys())

        # Update the proposal participation data
        holder_num = total_number_of_holders
        whale_num = len(total_whale_set | whale_votable_contract_no_delegate)
        non_whale_num = len(
            total_non_whale_set | non_whale_votable_contract_no_delegate
        )
        proposal_participation["holder_num"] = holder_num
        proposal_participation["whale_num"] = whale_num
        proposal_participation["non_whale_num"] = non_whale_num

        for group in ["whale", "non_whale"]:
            # calculate the turnout rate
            proposal_participation[f"{group}_turnout"] = (
                proposal_participation[f"{group}_vote_num"]
                / proposal_participation[f"{group}_num"]
                if proposal_participation[f"{group}_num"] > 0
                else np.nan
            )
            # calculate the the reason rate
            proposal_participation[f"{group}_reason_rate"] = (
                proposal_participation[f"{group}_reason_num"]
                / proposal_participation[f"{group}_vote_num"]
                if proposal_participation[f"{group}_vote_num"] > 0
                else np.nan
            )
        if (
            proposal_participation["whale_turnout"] > 1
            or proposal_participation["non_whale_turnout"] > 1
        ):
            continue

        # Append the proposal participation data
        df_proposals_participation.append(proposal_participation)
        # if whale_vote and non_whale_vote:
        #     break

    df_proposals_participation = pd.DataFrame(df_proposals_participation)

    # Calculate delegation turn out ratio
    for group in ["non_whale", "whale"]:
        df_proposals_participation[f"{group}_delegation_turnout"] = (
            df_proposals_participation.apply(
                lambda row: (
                    row[f"{group}_from_delegation_rate"] / row[f"{group}_turnout"]
                    if row[f"{group}_turnout"] > 0
                    else 0
                ),
                axis=1,
            )
        )

    # Calculate the winning metrics
    df_proposals_participation["non_whale_victory_vn"] = (
        (df_proposals_participation["non_whale_win_vn"] == 1)
        & (df_proposals_participation["whale_win_vn"] == 0)
    ).astype(int)

    df_proposals_participation["non_whale_victory_vp"] = (
        (df_proposals_participation["non_whale_win_vp"] == 1)
        & (df_proposals_participation["whale_win_vp"] == 0)
    ).astype(int)

    df_proposals_participation["non_whale_victory_vp_vn"] = (
        (df_proposals_participation["non_whale_victory_vn"] == 1)
        & (df_proposals_participation["whale_win_vp"] == 0)
    ).astype(int)

    df_proposals_participation = df_proposals_participation[
        ["id", "space"]
        # Participation metrics
        + [
            col
            for _ in ["whale", "non_whale"]
            for col in [
                f"{_}_num",
                f"{_}_vote_num",
                f"{_}_turnout",
                f"{_}_vs_hhi",
                f"{_}_vn_hhi",
                f"{_}_delegation_turnout",
                f"{_}_reason_rate",
                f"{_}_timing_avg",
            ]
        ]
        # Delegation metrics
        + [
            col
            for direction in ["from", "to"]
            for _ in ["whale", "non_whale"]
            for col in [
                f"{_}_{direction}_delegation_rate",
                f"{_}_{direction}_delegation_num",
            ]
        ]
        # Winning metrics
        + ["non_whale_victory_vn", "non_whale_victory_vp", "non_whale_victory_vp_vn"]
    ]

    # Turnout should be comparable to delegation rates
    for group in ["non_whale", "whale"]:
        for metric in ["num", "vote_num", "turnout"]:
            df_proposals_participation[f"{group}_{metric}"] = (
                df_proposals_participation.apply(
                    lambda row: (
                        np.nan
                        if np.isnan(row[f"{group}_from_delegation_rate"])
                        else row[f"{group}_{metric}"]
                    ),
                    axis=1,
                )
            )

    # # HHI and timing should be comparable between whales and non-whales
    # df_proposals_participation["non_whale_hhi"] = df_proposals_participation.apply(
    #     lambda row: (np.nan if np.isnan(row["whale_hhi"]) else row["non_whale_hhi"]),
    #     axis=1,
    # )

    # df_proposals_participation["non_whale_timing_avg"] = (
    #     df_proposals_participation.apply(
    #         lambda row: (
    #             np.nan
    #             if np.isnan(row["whale_timing_avg"])
    #             else row["non_whale_timing_avg"]
    #         ),
    #         axis=1,
    #     )
    # )
    # df_proposals_participation["non_whale_win"] = df_proposals_participation.apply(
    #     lambda row: (np.nan if np.isnan(row["whale_win"]) else row["non_whale_win"]),
    #     axis=1,
    # )
    # df_proposals_participation["whale_win"] = df_proposals_participation.apply(
    #     lambda row: (np.nan if np.isnan(row["non_whale_win"]) else row["whale_win"]),
    #     axis=1,
    # )
    df_proposals_participation.to_csv(
        PROCESSED_DATA_DIR / "proposals_voter.csv", index=False
    )
