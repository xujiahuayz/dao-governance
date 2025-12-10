"""Script to fetch governance token transfer"""

from ast import literal_eval
import time
import os
import json
from typing import Optional
import multiprocessing

import glob
import pandas as pd
from tqdm import tqdm
from web3 import HTTPProvider, Web3
from web3.exceptions import Web3RPCError

from governenv.constants import (
    PROCESSED_DATA_DIR,
    ABI_DIR,
    DATA_DIR,
    INFURA_API_BASE,
    CURRENT_BLOCK,
    STAKING_TOKEN,
)
from governenv.utils import (
    _fetch_events_for_all_contracts,
    to_dict,
)

INFURA_API_KEYS = os.getenv("INFURA_API_KEYS", "").split(",")
STEP = 100000


def split_blocks(
    start: int, end: int, step: int, address: str
) -> list[tuple[int, int]]:
    """
    Split the blocks into start and end ranges
    """

    min_block = (start // step) * step
    max_block = (end // step) * step

    block_ranges = []
    for b in range(min_block, max_block + step, step):
        if b < start:
            if os.path.exists(
                f"{DATA_DIR}/transfer/{address}/{start}_{b + step - 1}.jsonl"
            ):
                continue
            block_ranges.append((start, b + step - 1))
        elif b + step > end:
            if os.path.exists(f"{DATA_DIR}/transfer/{address}/{b}_{end}.jsonl"):
                continue
            block_ranges.append((b, end))
        else:
            if os.path.exists(
                f"{DATA_DIR}/transfer/{address}/{b}_{b + step - 1}.jsonl"
            ):
                continue
            block_ranges.append((b, b + step - 1))

    return block_ranges


def fetch_transfer_multiprocess(
    from_block: int,
    to_block: int,
    address: str,
    api_queue: multiprocessing.Queue,
    path: str,
    abi: dict[str, str],
) -> None:
    """Fetch the transfer events for all governance tokens using multiprocessing"""
    http = api_queue.get()
    fetch_transfer(
        from_block,
        to_block,
        address,
        http,
        path,
        abi,
    )
    api_queue.put(http)


def fetch_transfer(
    from_block: int,
    to_block: int,
    address: str,
    http: str,
    path: str,
    abi: dict[str, str],
    is_main: bool = True,
    temp_data: Optional[list] = None,
) -> bool:
    """Fetch the transfer events for all governance tokens"""
    if temp_data is None:
        temp_data = []

    success = True

    # Initialize web3
    w3 = Web3(HTTPProvider(http))
    checksum = Web3.to_checksum_address(address)
    contract = w3.eth.contract(address=checksum, abi=abi)
    transfer_event = contract.events.Transfer

    try:
        time.sleep(1)
        events = _fetch_events_for_all_contracts(
            w3,
            transfer_event,
            {"address": Web3.to_checksum_address(address)},
            from_block,
            to_block,
        )
        temp_data.extend(to_dict(events))
    except Web3RPCError as e:
        try:
            error_msg = json.loads(e.args[0].replace("'", '"'))
            if error_msg.get("code") == -32005:
                mid_block = (from_block + to_block) // 2
                left_ok = fetch_transfer(
                    from_block,
                    mid_block,
                    address,
                    http,
                    path,
                    abi,
                    False,
                    temp_data,
                )
                right_ok = fetch_transfer(
                    mid_block + 1,
                    to_block,
                    address,
                    http,
                    path,
                    abi,
                    False,
                    temp_data,
                )
                success = left_ok and right_ok
        except json.JSONDecodeError as e:
            print(
                f"Error fetch {address} events for block r````ange {from_block}-{to_block}: {e}"
            )
            success = False
        except Exception as e:
            print(
                f"Error fetch {address} events for block range {from_block}-{to_block}: {e}"
            )
            success = False
    except Exception as e:
        print(
            f"Error fetch {address} events for block range {from_block}-{to_block}: {e}"
        )
        success = False

    if is_main and success:
        with open(path, "w", encoding="utf-8") as f:
            for item in temp_data:
                f.write(json.dumps(item) + "\n")

    return success


if __name__ == "__main__":

    finish_files = set(
        file.split("/")[-1] for file in glob.glob(f"{DATA_DIR}/transfer/*")
    )

    with open(ABI_DIR / "erc20.json", "r", encoding="utf-8") as f:
        abi = json.load(f)

    df_proposals_with_sc = pd.read_csv(PROCESSED_DATA_DIR / "proposals_with_sc.csv")
    df_proposals_with_sc["address"] = df_proposals_with_sc["address"].apply(
        literal_eval
    )
    token_set = set()

    # Add governance tokens
    for idx, row in df_proposals_with_sc.iterrows():
        for token in row["address"]:
            token_set.add((token["address"], token["decimal"], token["blockNumber"]))

    # Add staking tokens
    for staking_address, info in STAKING_TOKEN.items():
        token_set.add((info["address"], info["decimal"], info["blockNumber"]))

    # token_set = [t for t in token_set if f"{t[0]}" not in finish_files]
    for address, _, start_block in tqdm(token_set):
        end_block = CURRENT_BLOCK
        blocks = split_blocks(start_block, end_block, STEP, address)
        print(f"Fetching transfer for {address} at blocks {blocks}")
        with multiprocessing.Manager() as manager:
            api_queue = manager.Queue()

            for api_key in INFURA_API_KEYS:
                api_queue.put(INFURA_API_BASE + api_key)

            os.makedirs(f"{DATA_DIR}/transfer/{address}", exist_ok=True)

            blocks = split_blocks(start_block, end_block, STEP, address)
            if len(blocks) == 0:
                continue

            num_processes = min(len(INFURA_API_KEYS), os.cpu_count())

            with multiprocessing.Pool(processes=num_processes) as pool:
                pool.starmap(
                    fetch_transfer_multiprocess,
                    [
                        (
                            *block_range,
                            address,
                            api_queue,
                            f"{DATA_DIR}/transfer/{address}/{block_range[0]}_{block_range[1]}.jsonl",
                            abi,
                        )
                        for block_range in blocks
                    ],
                )
