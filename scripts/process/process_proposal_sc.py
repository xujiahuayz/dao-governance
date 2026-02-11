"""Script to merge adjusted proposals with smart contract data."""

import json
import os
from ast import literal_eval

import pandas as pd
from web3 import Web3
from tqdm import tqdm

from governenv.constants import PROCESSED_DATA_DIR, INFURA_ENDPOINT, ABI_DIR
from governenv.etherscan import Etherscan
from governenv.utils import get_token_decimal

# Initialize web3
w3 = Web3(Web3.HTTPProvider(INFURA_ENDPOINT))
with open(ABI_DIR / "erc20.json", "r", encoding="utf-8") as f:
    abi = json.load(f)
ETHERSCAN_API_KEY = os.getenv("ETHERSCAN_API_KEY")
etherscan = Etherscan(api_key=ETHERSCAN_API_KEY)

df_proposals = pd.read_csv(PROCESSED_DATA_DIR / "proposals_event_study.csv")
df_proposals["strategies"] = df_proposals["strategies"].apply(literal_eval)

# filter to only ethereum erc20-balance-of proposals
df_proposals = df_proposals.loc[df_proposals["network_name"] == "Ethereum"]


# proposals with only erc20-balance-of strategy on Ethereum
df_proposals_erc20 = df_proposals.loc[
    df_proposals["strategies"].map(
        lambda strategies: set(strategy["name"] for strategy in strategies)
        == {"erc20-balance-of"}
        and set(strategy["network"] for strategy in strategies) == {"1"}
    )
].copy()
df_proposals_erc20["delegation"] = "no"
df_proposals_erc20["strategies_params"] = df_proposals_erc20["strategies"].apply(
    lambda strategies: [strategy["params"] for strategy in strategies]
)

# proposals with erc20-balance-of and delegation strategies on Ethereum
df_proposals_erc20_delegation = df_proposals.loc[
    df_proposals["strategies"].map(
        lambda strategies: set(strategy["name"] for strategy in strategies)
        == {"erc20-balance-of", "delegation"}
        and set(strategy["network"] for strategy in strategies) == {"1"}
    )
].copy()
df_proposals_erc20_delegation["delegation"] = "delegation"
df_proposals_erc20_delegation["strategies_params"] = df_proposals_erc20_delegation[
    "strategies"
].apply(
    lambda strategies: [
        strategy["params"]
        for strategy in strategies
        if strategy["name"] == "erc20-balance-of"
    ]
)

df_proposals_with_sc = pd.concat(
    [df_proposals_erc20, df_proposals_erc20_delegation], ignore_index=True
)

# keep proposals with valid address and decimal info
df_proposals_with_sc["address"] = df_proposals_with_sc["strategies_params"].apply(
    lambda params: (
        [{"address": p["address"].lower(), "decimal": p["decimals"]} for p in params]
        if "decimals" in params[0]
        else None
    )
)
df_proposals_with_sc = df_proposals_with_sc.dropna(subset=["address"])

token_dict = {}
for idx, row in df_proposals_with_sc.iterrows():
    for token in row["address"]:
        token_dict[token["address"]] = {
            "decimal": token["decimal"],
        }

token_block_dict = {}
for address, _ in tqdm(token_dict.items()):
    res = etherscan.get_contract_creation(
        contract_address=address,
    )
    creation_info = res[address][0] if res[address] else {}
    try:
        _ = get_token_decimal(w3, address, abi)
    except Exception as e:
        print(f"Error getting token decimal for {address}: {e}")
        continue

    token_block_dict[address] = {
        "blockNumber": int(creation_info["blockNumber"]),
        "decimal": token_dict[address]["decimal"],
    }

df_proposals_with_sc_list = []
for idx, row in df_proposals_with_sc.iterrows():
    address = row["address"]
    have_non_erc20 = False
    for idx, token in enumerate(address):
        token_address = token["address"]
        if token_address in token_block_dict:
            address[idx]["blockNumber"] = token_block_dict[token_address]["blockNumber"]
        else:
            have_non_erc20 = True

    if not have_non_erc20:
        row["address"] = address
        df_proposals_with_sc_list.append(row)

df_proposals_with_sc = pd.DataFrame(df_proposals_with_sc_list)
df_proposals_with_sc.to_csv(
    PROCESSED_DATA_DIR / "proposals_with_sc.csv",
    index=False,
)
