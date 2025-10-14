"""Script to merge adjusted proposals with smart contract data."""

import os
from ast import literal_eval
import gzip
import json

import numpy as np
import pandas as pd
from tqdm import tqdm
from web3 import Web3

from scripts.process_event_study import df_proposals_adj

from governenv.constants import PROCESSED_DATA_DIR, INFURA_ENDPOINT, ABI_DIR
from governenv.etherscan import Etherscan
from governenv.utils import get_token_decimal

ETHERSCAN_API_KEY = os.getenv("ETHERSCAN_API_KEY")
etherscan = Etherscan(api_key=ETHERSCAN_API_KEY)

MANUAL_CORRECTIONS = {
    "apecoin": "0x4d224452801ACEd8B2F0aebE155379bb5D594381",
    "icecream": "0x2ba592f78db6436527729929aaf6c908497cb200",
}
NON_ETHEREUM = ["gyroscope-gyd", "vaultcraft"]

SNAPSHOT_GECKO_NETWORK_MAPPING = {
    "Ethereum": "ethereum",
    "Polygon": "polygon-pos",
    "Arbitrum One": "arbitrum-one",
    "Base": "base",
    "Linea": "linea",
    "BNB Smart Chain": "binance-smart-chain",
    "Fantom Opera": "fantom",
    # "Sonic": "sonic",
    "Celo": "celo",
    "Core Blockchain": "core",
    # "Gnosis":
    "Harmony Shard 0": "harmony-shard-0",
    # "DFK Chain":
    "OP": "optimistic-ethereum",
    "PulseChain": "pulsechain",
    "Fraxtal": "fraxtal",
    "Metis Andromeda": "metis-andromeda",
    "Beam": "beam",
    "Moonbeam": "moonbeam",
    "Avalanche C-Chain": "avalanche",
    "Sei": "sei-network",
    "Ink": "ink",
    "zkSync": "zksync",
    "zkLink Nova": "zklink-nova",
}


# Load the space data
df_spaces = pd.read_csv(PROCESSED_DATA_DIR / "spaces_gecko.csv")
df_spaces = df_spaces[["coingecko", "strategies"]].rename(
    columns={"strategies": "space_strategies", "coingecko": "gecko_id"}
)
df_spaces["space_strategies"] = df_spaces["space_strategies"].apply(literal_eval)
df_proposals_adj = df_proposals_adj.merge(
    df_spaces,
    on="gecko_id",
    how="left",
)

# Use the coingecko id - smart contract mapping
with gzip.open(
    PROCESSED_DATA_DIR / "coingecko_id_smart_contract.json.gz",
    "rt",
    encoding="utf-8",
) as f:
    id_sc = json.load(f)

df_proposals_adj_sc = []
for idx, row in df_proposals_adj.iterrows():
    gecko_id = row["gecko_id"]
    if gecko_id in id_sc and "ethereum" in id_sc[gecko_id]:
        row["address_gecko"] = id_sc[gecko_id]["ethereum"]["contract_address"]
        row["network_gecko"] = "ethereum"
    else:
        row["address_gecko"] = None
        row["network_gecko"] = None
    df_proposals_adj_sc.append(row)
df_proposals_adj = pd.DataFrame(df_proposals_adj_sc)


# Use the snapshot smart contract data
df_proposals_adj["address_snapshot"] = df_proposals_adj["space_strategies"].apply(
    lambda strategies: [
        _
        for _ in strategies
        if _["network"] == "1" and "params" in _ and "address" in _["params"]
    ]
)
df_proposals_adj["address_snapshot"] = df_proposals_adj["address_snapshot"].apply(
    lambda x: x[0]["params"]["address"] if x else None
)

# Keep only the first occurrence of each gecko_id
df_proposals_adj["address"] = df_proposals_adj["address_gecko"].combine_first(
    df_proposals_adj["address_snapshot"]
)

# Apply manual corrections
for gecko_id, address in MANUAL_CORRECTIONS.items():
    df_proposals_adj.loc[df_proposals_adj["gecko_id"] == gecko_id, "address"] = address

df_sc = df_proposals_adj.drop_duplicates("gecko_id").dropna(subset=["address"])

# Initialize web3
w3 = Web3(Web3.HTTPProvider(INFURA_ENDPOINT))
with open(ABI_DIR / "erc20.json", "r", encoding="utf-8") as f:
    abi = json.load(f)


df_sc_creation = []
for idx, row in tqdm(df_sc.iterrows(), total=df_sc.shape[0]):
    address = row["address"].lower()
    res = etherscan.get_contract_creation(
        contract_address=address,
    )
    creation_info = res[address][0] if res[address] else {}
    row["blockNumber"] = creation_info["blockNumber"]
    try:
        row["decimal"] = get_token_decimal(w3, address, abi)
    except Exception as e:
        print(f"Error getting token decimal for {address}: {e}")
    df_sc_creation.append(row)

df_sc = pd.DataFrame(df_sc_creation)

# set the address of non-ethereum manual check
for gecko_id in NON_ETHEREUM:
    df_sc.loc[df_sc["gecko_id"] == gecko_id, "decimal"] = np.nan

# drop missing decimal to filter out non-ERC20 tokens
df_sc = df_sc.dropna(subset=["decimal"])

df_sc["address"] = df_sc["address"].str.lower()

df_sc.to_csv(
    PROCESSED_DATA_DIR / "proposals_adjusted_with_sc.csv",
    index=False,
)
