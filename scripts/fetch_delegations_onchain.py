"""
Script to fetch new pool data
"""

import gzip
import json
import time

from web3 import Web3
from web3.providers import HTTPProvider
from tqdm import tqdm

from governenv.constants import (
    ABI_DIR,
    INFURA_ENDPOINT,
    SNAPSHOT_DELEGATION_ADDRESS,
    SNAPSHOT_DELEGATION_START_BLOCK,
    DATA_DIR,
)
from governenv.utils import _fetch_events_for_all_contracts, to_dict

w3 = Web3(HTTPProvider(INFURA_ENDPOINT))


def current_block() -> int:
    """Get the current block number"""
    return w3.eth.block_number


def split_blocks(start_block: int, end_block: int, step: int) -> list[tuple[int, int]]:
    """Split blocks into smaller chunks"""
    if step <= 0:
        raise ValueError("step must be positive")
    if start_block > end_block:
        return []
    blocks: list[tuple[int, int]] = []
    s = start_block
    while s <= end_block:
        e = min(s + step - 1, end_block)
        blocks.append((s, e))
        s = e + 1
    return blocks


with open(ABI_DIR / "snapshot_delegation.json", "r", encoding="utf-8") as fh:
    abi = json.load(fh)
contract = w3.eth.contract(address=SNAPSHOT_DELEGATION_ADDRESS, abi=abi)

tip = current_block()
event_dict = {
    "set_delegate": contract.events.SetDelegate,
    "clear_delegate": contract.events.ClearDelegate,
}

for name, delegate_event in event_dict.items():
    with gzip.open(
        f"{DATA_DIR}/snapshot_{name}_onchain.jsonl.gz", "wt", encoding="utf-8"
    ) as f:
        for start, end in tqdm(
            split_blocks(
                SNAPSHOT_DELEGATION_START_BLOCK,
                tip,
                100_000,
            )
        ):
            time.sleep(2)
            events = to_dict(
                _fetch_events_for_all_contracts(
                    w3,
                    delegate_event,
                    {},
                    start,
                    end,
                )
            )
            for event in events:
                event["args"]["id"] = "0x" + event["args"]["id"].hex()
                f.write(json.dumps(event) + "\n")
