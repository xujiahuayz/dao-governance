"""Script to process delegation data."""

from typing import Literal

import os
import json
import gzip
import pandas as pd
from tqdm import tqdm

from governenv.constants import DATA_DIR, PROCESSED_DATA_DIR


def load_delegation_data(delegation_type: Literal["set", "clear"]):
    """Load delegation data from JSONL gzip files."""

    with gzip.open(
        DATA_DIR / f"snapshot_{delegation_type}_delegate_onchain.jsonl.gz",
        "rt",
        encoding="utf-8",
    ) as f:
        delegations = [json.loads(line) for line in f.readlines()]

    df_delegations = {
        "delegator": [],
        "delegatee": [],
        "space": [],
        "blockNumber": [],
        "transactionIndex": [],
        "logIndex": [],
    }
    for delegation in delegations:
        # id is the hex to string representation of space
        if (
            delegation["args"]["id"]
            == "0x0000000000000000000000000000000000000000000000000000000000000000"
        ):
            df_delegations["space"].append("all")
        else:
            try:
                df_delegations["space"].append(
                    bytes.fromhex(delegation["args"]["id"][2:])
                    .decode("utf-8")
                    .rstrip("\x00")
                )
            except Exception:  # pylint: disable=broad-except
                continue

        df_delegations["delegator"].append(delegation["args"]["delegator"].lower())
        df_delegations["delegatee"].append(delegation["args"]["delegate"].lower())
        df_delegations["blockNumber"].append(delegation["blockNumber"])
        df_delegations["transactionIndex"].append(delegation["transactionIndex"])
        df_delegations["logIndex"].append(delegation["logIndex"])

    df_delegations = pd.DataFrame(df_delegations)
    df_delegations["type"] = delegation_type

    return df_delegations


def save_snapshot(block_val: int, state: dict):
    """Save delegation snapshot at a specific block."""
    out = PROCESSED_DATA_DIR / "delegation" / f"delegation_{block_val}.json"
    with open(out, "w", encoding="utf-8") as f:
        json.dump(state, f, indent=2, sort_keys=True)


if __name__ == "__main__":

    os.makedirs(PROCESSED_DATA_DIR / "delegation", exist_ok=True)
    df_proposals = pd.read_csv(PROCESSED_DATA_DIR / "proposals_with_sc_blocks.csv")
    df_proposals = df_proposals.loc[df_proposals["delegation"] == "delegation"]
    df_proposals.dropna(subset=["created_ts_block"], inplace=True)
    block_set = set(df_proposals["created_ts_block"].unique().tolist())
    targets_sorted = sorted(block_set)
    target_idx = 0
    target = targets_sorted[target_idx]

    df_delegations = pd.concat(
        [
            load_delegation_data("set"),
            load_delegation_data("clear"),
        ],
        ignore_index=True,
    )
    df_delegations[["blockNumber", "transactionIndex", "logIndex"]] = df_delegations[
        ["blockNumber", "transactionIndex", "logIndex"]
    ].astype(int)
    df_delegations = df_delegations.sort_values(
        by=["blockNumber", "transactionIndex", "logIndex"],
        ascending=[True, True, True],
        kind="mergesort",
    ).reset_index(drop=True)

    delegation_set = {}
    for _, row in tqdm(df_delegations.iterrows(), total=len(df_delegations)):
        delegator = row["delegator"]
        idx = row["space"]
        delegatee = row["delegatee"]
        block_number = row["blockNumber"]

        while block_number > target:
            save_snapshot(target, delegation_set)

            # Move to the next target block
            target_idx += 1
            if target_idx >= len(targets_sorted):
                break
            target = targets_sorted[target_idx]

        if target_idx >= len(targets_sorted):
            break

        if delegator not in delegation_set:
            delegation_set[delegator] = {}

        if row["type"] == "set":
            delegation_set[delegator][idx] = delegatee
        elif row["type"] == "clear":
            if idx in delegation_set[delegator]:
                del delegation_set[delegator][idx]
            if not delegation_set[delegator]:
                del delegation_set[delegator]

    # Flush remaining targets after the last delegation event
    while target_idx < len(targets_sorted):
        print("Flushing target block:", targets_sorted[target_idx])
        save_snapshot(targets_sorted[target_idx], delegation_set)
        target_idx += 1
