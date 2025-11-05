"""Script to process the transfer data"""

from ast import literal_eval
import os
import glob
import json

import pandas as pd
from tqdm import tqdm

from governenv.constants import DATA_DIR, PROCESSED_DATA_DIR, STAKING_TOKEN


for name in ["transfer", "contract"]:
    os.makedirs(PROCESSED_DATA_DIR / name, exist_ok=True)

smart_contract = pd.read_csv(f"{DATA_DIR}/smart_contract_flipside.csv")
smart_contract = set(smart_contract["ADDRESS"].str.lower().tolist())

df_proposals_with_sc = pd.read_csv(
    PROCESSED_DATA_DIR / "proposals_with_sc.csv",
)
df_proposals_with_sc["address"] = df_proposals_with_sc["address"].map(literal_eval)
token_decimal = {}

# Add governance tokens
for addr_list in df_proposals_with_sc["address"]:
    for addr in addr_list:
        token_decimal[addr["address"].lower()] = addr["decimal"]

    # Add staking tokens
    for staking_address, info in STAKING_TOKEN.items():
        token_decimal[info["address"].lower()] = info["decimal"]

existing_files = glob.glob(f"{PROCESSED_DATA_DIR}/transfer/*.csv")
existing_files = [os.path.basename(i) for i in existing_files]
todo_tokens = set(token_decimal.keys()) - set(
    [i.replace(".csv", "") for i in existing_files]
)

for address, decimal in tqdm(token_decimal.items(), desc="Processing token transfers"):
    # process the transfer data
    if f"{address}.csv" in existing_files:
        continue

    files = glob.glob(f"{DATA_DIR}/transfer/{address}/*.jsonl")
    all_data = []
    for file in files:
        with open(file, "r", encoding="utf-8") as f:
            for line in f:
                item = json.loads(line)
                item["from"] = item["args"]["from"].lower()
                item["to"] = item["args"]["to"].lower()
                item["amount"] = int(item["args"]["amount"]) / (10**decimal)
                all_data.append(item)
    df = pd.DataFrame(all_data)
    if df.empty:
        continue
    df.drop(columns=["args"], inplace=True)
    df.sort_values("blockNumber", ascending=True, inplace=True)
    df.to_csv(PROCESSED_DATA_DIR / "transfer" / f"{address}.csv", index=False)

    # isolate the smart contract
    contract = []
    addresses = set(df["from"].tolist() + df["to"].tolist())
    for addr in addresses:
        if addr in smart_contract:
            contract.append(addr)
    # save the contract data
    pd.DataFrame({"address": contract}).to_csv(
        PROCESSED_DATA_DIR / "contract" / f"{address}.csv", index=False
    )
