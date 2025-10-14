"""Script to process the token holding"""

import json
from collections import defaultdict
import os

import pandas as pd

from tqdm import tqdm

from governenv.constants import PROCESSED_DATA_DIR, CURRENT_BLOCK
from scripts.process_event_study import df_proposals_adj


def build_snapshot(holding_dict: defaultdict, contract: set) -> dict:
    """Build the snapshot for each proposal."""
    snap = {k: v for k, v in holding_dict.items() if (k not in contract) and (v > 0)}
    snap = dict(sorted(snap.items(), key=lambda item: item[1], reverse=True))
    return snap


def save_snapshot(holding_dict: dict, address_str: str, block: int):
    """Save the snapshot to a json file."""
    with open(
        PROCESSED_DATA_DIR
        / "holding"
        / f"{address_str}"
        / f"{address_str}_{block}.json",
        "w",
        encoding="utf-8",
    ) as f:
        json.dump(holding_dict, f, indent=4)


# Merge token smart contract data
proposals_adjusted_with_sc = pd.read_csv(
    PROCESSED_DATA_DIR / "proposals_adjusted_with_sc.csv"
)[["gecko_id", "address", "decimal"]]
df_proposals_adj = (
    df_proposals_adj.merge(proposals_adjusted_with_sc, on="gecko_id", how="left")
    .dropna(subset="address")
    .sort_values(by=["gecko_id", "end_ts"], ascending=[True, True])
)

# Merge block data
df_block = pd.read_csv(
    PROCESSED_DATA_DIR / "proposals_adjusted_with_block.csv",
)
df_block = df_block[["id"] + [_ for _ in df_block.columns if "block" in _]]
df_proposals_adj = df_proposals_adj.merge(df_block, on="id", how="left")
df_proposals_adj = df_proposals_adj.loc[
    df_proposals_adj["end_ts_+5d_block"] <= CURRENT_BLOCK
]
df_proposals_adj.to_csv(
    PROCESSED_DATA_DIR / "proposals_adjusted_with_sc_block.csv", index=False
)

for address, group in tqdm(
    df_proposals_adj.groupby("address"), desc="Processing addresses"
):
    # Create a directory for the address if it doesn't exist
    os.makedirs(PROCESSED_DATA_DIR / "holding" / f"{address}", exist_ok=True)

    # Load ERC-20 transfer data
    df_transfer = pd.read_csv(PROCESSED_DATA_DIR / "transfer" / f"{address}.csv")

    # Load contract filter
    df_contract = pd.read_csv(PROCESSED_DATA_DIR / "contract" / f"{address}.csv")
    contract_set = set(df_contract["address"].str.lower().tolist())

    # Normalize addresses to lowercase
    for col in ("from", "to"):
        if col in df_transfer.columns:
            df_transfer[col] = df_transfer[col].str.lower()

    # Sort the transfer data by blockNumber, transactionIndex, and logIndex
    df_transfer = df_transfer.sort_values(
        by=[
            "blockNumber",
            "transactionIndex",
            "logIndex",
        ],
        ascending=True,
    )

    # Get the block numbers for token
    block_list = []
    for _, row in group.iterrows():
        for ts in ["start", "end", "created"]:
            for ts_block in [f"{ts}_ts_-5d", f"{ts}_ts_+5d", f"{ts}_ts"]:
                block_list.append(row[f"{ts_block}_block"])

    block_list = sorted(list(set(block_list)))

    # Make sure there are blocks to process
    if not block_list:
        raise ValueError(f"No blocks found for address {address}")

    # Interate through each proposal
    holding = defaultdict(float)
    for _, r in df_transfer.iterrows():

        # Get the current block number
        block_number = r["blockNumber"]

        # If there is no block left to process, break the loop
        if len(block_list) == 0:
            break

        # Get the list of blocks that are smaller than the current block number
        finished_block = [
            b for b in block_list if b is not None and int(b) < int(block_number)
        ]
        if len(finished_block) > 0:

            # filter the holding to remove contracts and negative holdings
            snapshot = build_snapshot(holding, contract_set)

            # save the current holding to all the finished blocks
            for b in finished_block:
                save_snapshot(snapshot, address, b)
                block_list.remove(b)

        # Update the holding based on the transfer event
        from_addr = r["from"]
        to_addr = r["to"]
        amount = r["amount"]
        holding[from_addr] -= amount
        holding[to_addr] += amount

    # --- Final flush: emit remaining blocks (covers == last processed block) ---
    if block_list:
        print(f"Final flush for {address}, {len(block_list)} blocks left")
        snapshot = build_snapshot(holding, contract_set)
        for b in list(block_list):
            save_snapshot(snapshot, address, b)
            block_list.remove(b)
