"""Script to process the token holding"""

from ast import literal_eval
import json
from collections import defaultdict
import os

import pandas as pd

from tqdm import tqdm

from governenv.constants import PROCESSED_DATA_DIR, STAKING_TOKEN, MIXED_TYPE_TOKEN


def build_snapshot(holding_dict: defaultdict, contract: set) -> dict:
    """Build the snapshot for each proposal."""
    # snap = {k: v for k, v in holding_dict.items() if (k not in contract) and (v > 0)}

    snap = {}
    for addr, holdings in holding_dict.items():
        snap[addr] = {"holding": holdings, "contract": addr in contract}

    # snap = dict(sorted(snap.items(), key=lambda item: item[1], reverse=True))
    snap = dict(sorted(snap.items(), key=lambda item: item[1]["holding"], reverse=True))
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


df_proposals_with_sc = pd.read_csv(
    PROCESSED_DATA_DIR / "proposals_with_sc.csv",
)

with open(PROCESSED_DATA_DIR / "snapshot_block.json", "r", encoding="utf-8") as f:
    snapshot_block = json.load(f)

# Map timestamp to block number
for ts in ["start", "end", "created"]:
    for ts_block in [f"{ts}_ts_-5d", f"{ts}_ts_+5d"]:
        df_proposals_with_sc[f"{ts_block}_block"] = df_proposals_with_sc[ts_block].map(
            lambda ts: snapshot_block[str(ts)]
        )
df_proposals_with_sc["created_ts_block"] = df_proposals_with_sc["created_ts"].map(
    lambda ts: snapshot_block[str(ts)]
)

df_proposals_with_sc["address"] = df_proposals_with_sc["address"].map(literal_eval)

# Remove mixed type tokens
df_proposals_with_sc = df_proposals_with_sc.loc[
    ~df_proposals_with_sc["address"].apply(
        lambda x: any(token["address"] in MIXED_TYPE_TOKEN for token in x)
    )
]

# Replace staking token address (dedupe by address)
rows = []
for _, row in df_proposals_with_sc.iterrows():
    # Use a dict keyed by address to avoid “dict in set” (unhashable) and dedupe cleanly
    by_addr = {}

    for tok in row["address"]:
        addr = tok["address"]

        if addr in STAKING_TOKEN:
            info = STAKING_TOKEN[addr]
            # Standardize keys; prefer 'decimals'
            by_addr[info["address"].lower()] = {
                "address": info["address"].lower(),
                "decimals": info["decimal"],
                "blockNumber": info["blockNumber"],
            }
        else:
            by_addr[addr.lower()] = {
                "address": addr.lower(),
                "decimals": tok["decimal"],
                "blockNumber": tok["blockNumber"],
            }

    # write back a list of unique tokens
    new_row = row.copy()
    new_row["address"] = list(by_addr.values())
    rows.append(new_row)

underlying_tokens = [v["address"] for _, v in STAKING_TOKEN.items()]
df_proposals_with_sc = pd.DataFrame(rows)

df_proposals_with_sc.to_csv(
    PROCESSED_DATA_DIR / "proposals_with_sc_blocks.csv",
    index=False,
)

# get token-block mapping
token_block = defaultdict(list)
for idx, row in df_proposals_with_sc.iterrows():
    for ts in ["start", "end", "created"]:
        for ts_block in [f"{ts}_ts_-5d", f"{ts}_ts_+5d"]:
            for address in row["address"]:
                token_block[address["address"]].append(row[f"{ts_block}_block"])

# de-deup and sort once
for address, block_list in token_block.items():
    token_block[address] = sorted(set(block_list))

for address, block_list in tqdm(
    token_block.items(),
    desc="Processing token holdings",
):
    df_transfer = pd.read_csv(PROCESSED_DATA_DIR / "transfer" / f"{address}.csv")
    staking_contract = [k for k, v in STAKING_TOKEN.items() if v["address"] == address]

    # Create a directory for the address if it doesn't exist
    os.makedirs(PROCESSED_DATA_DIR / "holding" / f"{address}", exist_ok=True)

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

        # Skip transfer if it is relevant to staking contracts, keep the initial holding unchanged
        if staking_contract and (
            (from_addr in staking_contract) or (to_addr in staking_contract)
        ):
            continue
        holding[from_addr] -= amount
        holding[to_addr] += amount

    # --- Final flush: emit remaining blocks (covers == last processed block) ---
    if block_list:
        print(f"Final flush for {address}, {len(block_list)} blocks left")
        snapshot = build_snapshot(holding, contract_set)
        for b in list(block_list):
            save_snapshot(snapshot, address, b)
            block_list.remove(b)
