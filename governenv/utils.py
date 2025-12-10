"""
Utility functions
"""

from datetime import datetime
import heapq
import re
from typing import Any, Iterable, Optional
from collections import defaultdict
from ast import literal_eval

from hexbytes import HexBytes
import jellyfish
import numpy as np
import pandas as pd
import requests

from eth_abi.codec import ABICodec
from web3 import Web3
from web3._utils.events import get_event_data
from web3._utils.filters import construct_event_filter_params
from web3.datastructures import AttributeDict
from web3.providers import HTTPProvider

from governenv.constants import EXKW, WHALE_THRESHOLD


def kw_filt(url: str) -> bool:
    """
    Function to filter discussions based on keywords
    """

    return not any(i in url for i in EXKW)


def slash_filt(data: dict[str, str]) -> dict[str, str]:
    """
    Function to filter discussions based on slashes
    """

    # typically, a discussion has at least 4 levels of slashes
    # if the slash count is less than 4, remove the discussion
    return {k: v for k, v in data.items() if v.count("/") >= 4}


# Fuzzy Matching
PUNC = """ |,|\.|;|:|\||\(|\)|&|'|"|\+|-|/"""

PHRASE_MAP = {
    "no objection": "yes",
}

REMOVE = [
    "",
    "dao",
    "amm",
    "vault",
    "vaults",
    "finance",
    "legacy",
    "protocol",
    "council",
    "sccp",
    "sip",
    "defi",
    "old",
    "main",
    "capital",
]


def remove_version(name: str, length: int) -> str:
    """Remove version information from the name."""
    if length > 1:
        return re.sub(r"\bv\d+(\.\d+)*\b", "", name)
    return name


def clean_name(name: str) -> str:
    """Clean the name by removing special characters and lowercasing."""

    # lowercase
    name = name.lower()

    # replace special characters with space
    name = name.replace("(", "").replace(")", "")

    # split by punctuation
    wname = re.split(PUNC, name)

    # remove version info
    wname = [remove_version(w, len(wname)) for w in wname if w not in REMOVE]

    return " ".join([w for w in wname if w]).strip()


def match_top(s, candidates, n=1, method="lev"):
    """Match the top n candidates from the list."""
    heap = [(-np.inf, "") for _ in range(n)]
    heapq.heapify(heap)

    for t in candidates:
        l = len(t)
        if method == "lev":
            score = jellyfish.levenshtein_distance(s, t) / max(l, len(s)) - 1
        elif method == "dam_lev":
            score = jellyfish.damerau_levenshtein_distance(s, t) / max(l, len(s)) - 1
        elif method == "jaro":
            score = -jellyfish.jaro_distance(s, t)
        elif method == "jaro_win":
            score = -jellyfish.jaro_winkler_similarity(s, t)

        heapq.heappushpop(heap, (-score, t))

    heap.sort(reverse=True)
    return heap


def match_keywords(text: str, keywords: set[str]) -> bool:
    """Check if any of the keywords are in the text."""
    if not isinstance(text, str):
        return False

    # lowercase, normalize apostrophes
    s = text.lower().replace("’", "'")

    # map phrases
    for phrase, replacement in PHRASE_MAP.items():
        s = s.replace(phrase, replacement)

    # tokenize into words
    tokens = set(re.findall(r"\b\w+\b", s))

    # check intersection
    return len(tokens & keywords) > 0


def word_count(text: str) -> int:
    """Count the number of words in a text."""
    if not isinstance(text, str):
        return 0
    return len(text.strip().split())


# Web3 related utilities
def to_dict(obj: Any) -> Any:
    """Convert an AttributeDict to a regular dictionary"""
    if isinstance(obj, AttributeDict):
        return {k: to_dict(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [to_dict(item) for item in obj]
    elif isinstance(obj, HexBytes):
        return "0x" + obj.hex()
    return obj


def fetch_current_block(http: str) -> int:
    """Fetch the current block number"""

    w3 = Web3(HTTPProvider(http))

    return w3.eth.block_number


def fetch_erc20_balance_of(
    w3: Web3, token_address: str, holder_address: str, block: int, abi: dict
) -> int:
    """Fetch the ERC-20 balance of a holder"""

    token_contract = w3.eth.contract(
        address=Web3.to_checksum_address(token_address), abi=abi
    )
    return token_contract.functions.balanceOf(
        Web3.to_checksum_address(holder_address)
    ).call(block_identifier=block)


def _fetch_events_for_all_contracts(
    w3: Web3,
    event: Any,
    argument_filters: dict[str, Any],
    from_block: int,
    to_block: int,
) -> Iterable[dict[str, Any]]:
    """Method to get events

    Args:
        w3 (Web3): The Web3 instance
        event (Any): The event to fetch
        argument_filters (dict[str, Any]): The filters to apply to the event
        from_block (int): The block number to start fetching events from, inclusive
        to_block (int): The block number to stop fetching events from, inclusive
    """

    if from_block is None:
        raise ValueError("Missing mandatory keyword argument 'from_block'")

    # Construct the event filter parameters
    abi = event._get_event_abi()
    codec: ABICodec = w3.codec
    _, event_filter_params = construct_event_filter_params(
        abi,
        codec,
        address=argument_filters.get("address"),
        argument_filters=argument_filters,
        from_block=from_block,
        to_block=to_block,
    )

    # logging
    logs = w3.eth.get_logs(event_filter_params)

    all_events = []
    for log in logs:
        evt = get_event_data(codec, abi, log)
        all_events.append(evt)

    return all_events


def get_token_decimal(w3: Web3, token_address: str, abi: dict) -> int:
    """Get the decimal of a token"""

    token_contract = w3.eth.contract(
        address=Web3.to_checksum_address(token_address), abi=abi
    )
    return token_contract.functions.decimals().call()


def get_block_by_timestamp(target_block: int) -> Optional[int]:
    """
    Function to get the block by timestamp
    """

    length = 0
    result = {"timestamp": None, "height": None}

    while length == 0:
        result = requests.get(
            f"https://coins.llama.fi/block/ethereum/{target_block}", timeout=60
        ).json()
        length = len(result)

    return result["height"]


def get_blocks_by_timestamps(start_date: str, end_date: str) -> Iterable:
    """
    Function to get the blocks by timestamps
    """

    timestamp_list = get_date_range(start_date, end_date)

    for timestamp in timestamp_list:
        yield (unix_to_timestamp(timestamp), get_block_by_timestamp(timestamp))


def timestamp_to_unix(timestamp: str) -> int:
    """
    Function to convert timestamp to unix
    """

    return int(datetime.strptime(timestamp, "%Y-%m-%d").timestamp())


def unix_to_timestamp(unix: int) -> str:
    """
    Function to convert unix to timestamp
    """

    return datetime.fromtimestamp(unix).strftime("%Y-%m-%d")


def get_date_range(start_date: str, end_date: str):
    """
    Function to get the date range
    """

    return [
        timestamp_to_unix(_)
        for _ in pd.date_range(start=start_date, end=end_date, freq="D").strftime(
            "%Y-%m-%d"
        )
    ]


# Math
def standardized_hhi(counts: list) -> float:
    """Function to calculate standardized HHI."""
    if len(counts) == 0:
        return np.nan
    total = sum(counts)
    if total == 0:
        return np.nan
    hhi = sum((count / total) ** 2 for count in counts)
    n = len(counts)
    if n == 1:
        return 1.0
    std_hhi = (hhi - (1 / n)) / (1 - (1 / n))

    std_hhi = max(std_hhi, 0.0)

    # threshold tiny values
    if std_hhi < 1e-4:
        std_hhi = 0.0

    return std_hhi


def calc_frequency(choices: list) -> defaultdict:
    """Function to calculate choice frequency."""
    frequency = defaultdict(int)
    for c in choices:
        frequency[c] += 1
    return frequency


def calc_vp(choices: list, vps: list) -> defaultdict:
    """Function to calculate choice vp."""
    vp_dict = defaultdict(float)
    for idx, c in enumerate(choices):
        vp_dict[c] += vps[idx]
    return vp_dict


def calc_delegation(
    records: list,
    directions: str,
    groups: str,
    total_holdings: float,
) -> int:
    """Function to calculate delegation counts."""

    direction_str = "delegator" if directions == "from" else "delegatee"
    if groups == "whale":
        filtered_set = set(
            record[direction_str]
            for record in records
            if record[f"{direction_str}_holding"] >= (WHALE_THRESHOLD * total_holdings)
        )
    else:
        filtered_set = set(
            record[direction_str]
            for record in records
            if record[f"{direction_str}_holding"] < (WHALE_THRESHOLD * total_holdings)
        )
    return len(filtered_set)


def process_vote(df: pd.DataFrame) -> pd.DataFrame:
    """Function to process vote data"""

    df_list = []
    df["choice"] = df["choice"].apply(literal_eval)

    match df["type"].unique()[0]:
        case "dict":
            for _, row in df.iterrows():
                if len(row["choice"]) == 0:
                    continue
                all_weights = sum(row["choice"].values())
                for choice, weight in row["choice"].items():
                    row_copy = row.copy()
                    row_copy["choice"] = choice
                    row_copy["vp"] = weight / all_weights * row_copy["vp"]
                    df_list.append(row_copy)
            df = pd.DataFrame(df_list)
        case "list":
            for _, row in df.iterrows():
                if len(row["choice"]) == 0:
                    continue
                row["choice"] = row["choice"][0]
                df_list.append(row)
            df = pd.DataFrame(df_list)

    return df


def voter_split(
    df: pd.DataFrame,
    total_holding_data: dict,
    total_holding: float,
    start_ts: int,
    end_ts: int,
) -> tuple[dict, list]:
    """Split voters into whales and non-whales based on holding percentage."""
    voting = {}
    unknown_voters = []
    # iterate through voters
    for _, row in df.iterrows():
        voter = row["voter"]
        if voter in total_holding_data:
            holding = total_holding_data[voter]
            label = (
                "whales"
                if holding["holding"] >= (WHALE_THRESHOLD * total_holding)
                else "non_whales"
            )
            voting[voter] = {
                "label": label,
                "vp": row["vp"],
                "holding": holding["holding"],
                "contract": holding["contract"],
                "choice": row["choice"],
                "reason": 1 if pd.notna(row["reason"]) else 0,
                "created": row["created"],
                "timing": (int(row["created"]) - int(start_ts))
                / (int(end_ts) - int(start_ts)),
            }
        else:
            unknown_voters.append(
                {
                    "voter": voter,
                    "vp": row["vp"],
                }
            )

    return voting, unknown_voters


if __name__ == "__main__":
    import json
    from governenv.constants import ABI_DIR
    from governenv.settings import INFURA_API_KEY

    w3 = Web3(HTTPProvider(f"https://mainnet.infura.io/v3/{INFURA_API_KEY}"))

    with open(ABI_DIR / "erc20.json", "r", encoding="utf-8") as f:
        erc20_abi = json.load(f)

    balance = fetch_erc20_balance_of(
        w3,
        "0xC128a9954e6c874eA3d62ce62B468bA073093F25".lower(),
        "0x849d52316331967b6ff1198e5e32a0eb168d039d".lower(),
        14787732,
        erc20_abi,
    )
