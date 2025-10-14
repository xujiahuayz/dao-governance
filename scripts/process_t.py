"""Analyze transfer patterns around proposals (threaded, I/O-optimized)."""

from ast import literal_eval
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed
import json
import os
import pickle
import warnings
from pathlib import Path

import pandas as pd
from tqdm import tqdm

from governenv.constants import PROCESSED_DATA_DIR, WHALE_THRESHOLD

warnings.filterwarnings("ignore")

# ---------------------------
# Utilities
# ---------------------------


def _fast_read_csv(path, usecols=None, dtype=None):
    """Try pyarrow engine (faster) and fall back to default if unavailable."""
    try:
        return pd.read_csv(path, usecols=usecols, dtype=dtype, engine="pyarrow")
    except Exception:
        return pd.read_csv(path, usecols=usecols, dtype=dtype)


def _load_json_safe(path):
    """Load JSON file; return empty dict if missing or invalid."""
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return {}
    except Exception:
        # Malformed JSON or encoding error—treat as empty
        return {}


# ---------------------------
# Core logic
# ---------------------------


def agg_router(g: pd.DataFrame, tol: float = 1) -> pd.DataFrame:
    """
    Aggregate multi-hop router-like transactions within a single txn hash
    into direct source->sink flows that conserve amounts.
    Input g must have columns ["from", "to", "amount"] for a single txn.
    """
    # aggregate transfers between two nodes
    cap = defaultdict(lambda: defaultdict(float))
    for f, t, a in g[["from", "to", "amount"]].itertuples(index=False):
        cap[f][t] += float(a)

    # node balances
    out_amt = defaultdict(float)
    in_amt = defaultdict(float)
    for u in cap:
        for v, a in cap[u].items():
            out_amt[u] += a
            in_amt[v] += a

    remaining = {n: out_amt[n] - in_amt[n] for n in set(out_amt) | set(in_amt)}
    sources = {n: v for n, v in remaining.items() if v > 0}
    sinks = {n: -v for n, v in remaining.items() if v < 0}

    # trivial cases
    if len(sources) == 1 and len(sinks) == 1:
        s = next(iter(sources))
        t = next(iter(sinks))
        return pd.DataFrame({"from": [s], "to": [t], "amount": [sources[s]]})
    elif len(sources) == 1 and len(sinks) > 1:
        s = next(iter(sources))
        return pd.DataFrame(
            {
                "from": [s] * len(sinks),
                "to": list(sinks.keys()),
                "amount": list(sinks.values()),
            }
        )
    elif len(sources) > 1 and len(sinks) == 1:
        t = next(iter(sinks))
        return pd.DataFrame(
            {
                "from": list(sources.keys()),
                "to": [t] * len(sources),
                "amount": list(sources.values()),
            }
        )

    # proportional split for many-to-many
    total_src = sum(sources.values())
    total_sink = sum(sinks.values())
    if abs(total_src - total_sink) > tol:
        raise ValueError("Total source and sink amount do not match")

    flow = []
    for s, sa in sources.items():
        for t, ta in sinks.items():
            flow.append({"from": s, "to": t, "amount": sa * (ta / total_sink)})
    return pd.DataFrame(flow)


def process_proposal_group(
    address: str, group: pd.DataFrame, cex_dex: set
) -> pd.DataFrame | None:
    """Process all proposals for one token address; returns aggregated flow frame or None."""
    # --- Fast, narrow reads
    transfer_path = PROCESSED_DATA_DIR / "transfer" / f"{address}.csv"
    if not transfer_path.exists():
        return None

    # Keep only necessary columns + lean dtypes
    tx_dtypes = {
        "blockNumber": "int64",
        "transactionHash": "string",
        "from": "string",
        "to": "string",
        "amount": "float64",
    }
    df_transfer = _fast_read_csv(
        transfer_path,
        usecols=["blockNumber", "transactionHash", "from", "to", "amount"],
        dtype=tx_dtypes,
    )
    if df_transfer.empty:
        return None

    contract_path = PROCESSED_DATA_DIR / "contract" / f"{address}.csv"
    if contract_path.exists():
        df_contract = _fast_read_csv(
            contract_path, usecols=["address"], dtype={"address": "string"}
        )
        contract = set(df_contract["address"].dropna().tolist())
    else:
        contract = set()
    staking = contract.difference(cex_dex)

    out_frames = []

    # Iterate proposals (group is small per address)
    for _, proposal in group.iterrows():
        for stage in ("created", "end"):
            lower_block = proposal.get(f"{stage}_ts_-5d_block")
            upper_block = proposal.get(f"{stage}_ts_+5d_block")
            if pd.isna(lower_block) or pd.isna(upper_block):
                continue

            # Window the transfers
            df_stage_raw = df_transfer.loc[
                (df_transfer["blockNumber"] >= int(lower_block))
                & (df_transfer["blockNumber"] < int(upper_block))
            ]
            if df_stage_raw.empty:
                continue

            # Handle router transactions per txn hash
            stage_parts = []
            for _, g in df_stage_raw.groupby("transactionHash", sort=False):
                if len(g) >= 2:
                    df_router = agg_router(g[["from", "to", "amount"]])
                    stage_parts.append(df_router)
                else:
                    # Keep the row in a compatible schema
                    stage_parts.append(g[["from", "to", "amount"]])

            df_stage = pd.concat(stage_parts, ignore_index=True)
            if df_stage.empty:
                continue

            # Load lower/upper holdings (skip if missing)
            lower_json = (
                PROCESSED_DATA_DIR
                / "holding"
                / address
                / f"{address}_{int(lower_block)}.json"
            )
            upper_json = (
                PROCESSED_DATA_DIR
                / "holding"
                / address
                / f"{address}_{int(upper_block)}.json"
            )
            holding_lower = _load_json_safe(lower_json)
            holding_upper = _load_json_safe(upper_json)
            if not holding_lower or not holding_upper:
                # If either snapshot missing, skip this stage
                continue

            # Filter out CEX/DEX in holdings
            holding_lower = {k: v for k, v in holding_lower.items() if k not in cex_dex}
            holding_upper = {k: v for k, v in holding_upper.items() if k not in cex_dex}

            all_lower = sum(holding_lower.values()) or 0.0
            all_upper = sum(holding_upper.values()) or 0.0

            whale_lower = {
                k
                for k, v in holding_lower.items()
                if all_lower and v >= all_lower * WHALE_THRESHOLD
            }
            non_whale_lower = set(holding_lower).difference(whale_lower)

            whale_upper = {
                k
                for k, v in holding_upper.items()
                if all_upper and v >= all_upper * WHALE_THRESHOLD
            }
            non_whale_upper = set(holding_upper).difference(whale_upper)

            # Identity mapping for participants in this window
            participants = set(df_stage["from"]).union(set(df_stage["to"]))

            participants_whale = participants.intersection(whale_lower).union(
                participants.intersection(whale_upper)
            )
            participants_non_whale = participants.intersection(non_whale_lower).union(
                participants.intersection(non_whale_upper)
            )
            participants_cex_dex = participants.intersection(cex_dex)
            participants_staking = participants.intersection(staking)
            other_participants = participants.difference(
                participants_whale
                | participants_non_whale
                | participants_cex_dex
                | participants_staking
            )

            identities = {}
            identities.update({k: "whale" for k in participants_whale})
            identities.update({k: "non_whale" for k in participants_non_whale})
            identities.update({k: "cex_dex" for k in participants_cex_dex})
            identities.update({k: "smart_contract" for k in participants_staking})
            identities.update({k: "other" for k in other_participants})

            # Map identities
            df_stage["identity_from"] = df_stage["from"].map(identities)
            df_stage["identity_to"] = df_stage["to"].map(identities)

            # Aggregate by identity
            df_stage_agg = (
                df_stage.groupby(["identity_from", "identity_to"], dropna=False)[
                    "amount"
                ]
                .sum()
                .reset_index()
            )
            df_stage_agg["proposal_id"] = proposal["id"]
            df_stage_agg["stage"] = stage
            out_frames.append(df_stage_agg)

    if not out_frames:
        return None
    return pd.concat(out_frames, ignore_index=True)


# ---------------------------
# Threaded driver
# ---------------------------


def main():
    # Paths
    processed = Path(PROCESSED_DATA_DIR)

    # Load proposals with block & SC info
    df_proposals_adj = _fast_read_csv(
        processed / "proposals_adjusted_with_sc_block.csv"
    )
    if "scores" in df_proposals_adj.columns:
        df_proposals_adj["scores"] = df_proposals_adj["scores"].apply(literal_eval)

    # Group once (small groups per address; stored in-memory)
    groups_by_addr = {
        addr: g for addr, g in df_proposals_adj.groupby("address", sort=False)
    }
    addresses = list(groups_by_addr.keys())

    # Load CEX/DEX set
    with open(processed / "cex_dex.pkl", "rb") as f:
        cex_dex = pickle.load(f)
        if not isinstance(cex_dex, set):
            cex_dex = set(cex_dex)

    # Threaded execution—good for I/O workloads
    max_workers = min(8, (os.cpu_count() or 6))  # 4–8 is typically best for SSDs
    results = []

    with ThreadPoolExecutor(max_workers=max_workers) as ex:
        futures = {
            ex.submit(process_proposal_group, addr, groups_by_addr[addr], cex_dex): addr
            for addr in addresses
        }
        for fut in tqdm(
            as_completed(futures),
            total=len(futures),
            desc="Processing addresses",
            unit="addr",
        ):
            res = fut.result()
            if res is not None and not res.empty:
                results.append(res)

    if not results:
        print("No results produced.")
        return

    df_flow = pd.concat(results, ignore_index=True)

    # Focus on flows involving CEX/DEX
    df_txn = df_flow.loc[
        (df_flow["identity_from"] == "cex_dex") | (df_flow["identity_to"] == "cex_dex")
    ].copy()

    if df_txn.empty:
        print("No CEX/DEX-related flows found.")
        return

    # Per-proposal normalisation to percentages
    df_txn["amount_total"] = df_txn.groupby(["proposal_id", "stage"])[
        "amount"
    ].transform("sum")
    df_txn = df_txn[df_txn["amount_total"].ne(0)].copy()
    df_txn["amount_pct"] = df_txn["amount"] / df_txn["amount_total"]

    # Aggregate across proposals: mean share by stage & identity pair
    df_txn = (
        df_txn.groupby(["stage", "identity_from", "identity_to"], dropna=False)[
            "amount_pct"
        ]
        .mean()
        .reset_index()
    )

    # Example: write outputs (optional—uncomment if you want files)
    # out_dir = processed / "outputs"
    # out_dir.mkdir(exist_ok=True, parents=True)
    # df_flow.to_csv(out_dir / "cex_dex_flow_raw.csv", index=False)
    # df_txn.to_csv(out_dir / "cex_dex_flow_pct_mean.csv", index=False)

    # Print a small preview
    print("Aggregated CEX/DEX flow share (mean by stage & identity pair):")
    print(df_txn.head(20).to_string(index=False))


if __name__ == "__main__":
    main()
