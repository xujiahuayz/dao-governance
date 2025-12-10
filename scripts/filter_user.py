"""Filter out SC-related transfers."""

import numpy as np
import os
import json
import glob
from multiprocessing import Pool, cpu_count, get_context

from tqdm import tqdm
import pandas as pd

from governenv.constant import DATA_PATH, token_transfer_schema

N_WORKERS = 10

# Output folder
OUTPUT_DIR = f"{DATA_PATH}/dao/sc_transfer"
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Input files
INPUT_GLOB = f"{DATA_PATH}/ethereum/token_transfer/*.snappy.parquet"
token_files = sorted(glob.glob(INPUT_GLOB))

with open(f"{DATA_PATH}/space_contract.json", "r") as f:
    sc = json.load(f)

# Flatten contract list → set of addresses
SC_ADDRESSES = {addr.lower() for _, addrs in sc.items() for addr in addrs}

# Reverse lookup: address → space
ADDRESS_TO_SPACE = {
    addr.lower(): space for space, addrs in sc.items() for addr in addrs
}


def _process_one(token_file: str):
    """Process a single parquet token transfer file."""

    idx = os.path.basename(token_file).replace(".snappy.parquet", "")

    # read
    df = pd.read_parquet(token_file, engine="pyarrow")
    df.columns = token_transfer_schema

    # filter
    mask = (df["from_address"].isin(SC_ADDRESSES)) | (
        df["to_address"].isin(SC_ADDRESSES)
    )
    df = df[mask].copy()

    # add labels
    df["from_label"] = df["from_address"].map(ADDRESS_TO_SPACE)
    df["to_label"] = df["to_address"].map(ADDRESS_TO_SPACE)

    # export
    df.to_csv(f"{OUTPUT_DIR}/{idx}.csv", index=False)


def main():
    """Main function to filter SC-related transfers."""
    # multiprocessing with tqdm
    with get_context("spawn").Pool(N_WORKERS) as pool:
        for _ in tqdm(
            pool.imap_unordered(_process_one, token_files),
            total=len(token_files),
            desc="Processing",
        ):
            pass


if __name__ == "__main__":
    main()
