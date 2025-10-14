"""Fetch timestamps for many Ethereum blocks (single-thread, batched JSON-RPC)."""

import os
import gzip
import json
import time
from typing import Iterable

import requests
from dotenv import load_dotenv
from tqdm import tqdm

from governenv.constants import DATA_DIR

load_dotenv()

BATCH_SIZE = 100

ALCHEMY_HTTP_URL = "https://eth-mainnet.g.alchemy.com/v2/" + os.environ.get(
    "ALCHEMY_API_KEY", ""
)


def load_unique_blocks() -> list[int]:
    """Load unique block numbers from on-chain delegation events."""
    data = []
    for typ in ["set", "clear"]:
        with gzip.open(
            DATA_DIR / f"snapshot_{typ}_delegate_onchain.jsonl.gz", "rt"
        ) as f:
            for line in f:
                data.append(json.loads(line))
    return sorted({int(item["blockNumber"]) for item in data})


def chunked(seq: Iterable[int], size: int) -> Iterable[list[int]]:
    """Yield successive n-sized chunks from seq."""
    batch = []
    for x in seq:
        batch.append(x)
        if len(batch) >= size:
            yield batch
            batch = []
    if batch:
        yield batch


if __name__ == "__main__":
    blocks = load_unique_blocks()
    batches = list(chunked(blocks, BATCH_SIZE))
    with gzip.open(DATA_DIR / "block_ts.jsonl.gz", "at") as f:
        for batch in tqdm(batches, desc="Fetching block timestamps"):
            payload = [
                {
                    "jsonrpc": "2.0",
                    "id": f"blk-{b}",
                    "method": "eth_getBlockByNumber",
                    "params": [hex(b), False],
                }
                for b in batch
            ]
            res = r = requests.post(ALCHEMY_HTTP_URL, json=payload, timeout=60).json()
            if len(res) != len(batch):
                raise ValueError("Mismatched response length")
            for item in res:
                result = item.get("result") or {}
                num_hex = result.get("number")
                ts_hex = result.get("timestamp")
                if num_hex and ts_hex:
                    b = int(num_hex, 16)
                    t = int(ts_hex, 16)
                    f.write(json.dumps({"block": b, "timestamp": t}) + "\n")
            time.sleep(4)
