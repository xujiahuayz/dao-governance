"""Script to analyze the transfer pattern"""

from ast import literal_eval
from collections import defaultdict
import json
import pickle
import warnings


from tqdm import tqdm
import pandas as pd

from governenv.constants import PROCESSED_DATA_DIR, WHALE_THRESHOLD

warnings.filterwarnings("ignore")


def load_whale(token_address: str, block: int, cex_dex: set) -> dict:
    """Function to load the whale data from the json file"""
    with open(
        PROCESSED_DATA_DIR
        / "holding"
        / token_address
        / f"{token_address}_{block}.json",
        "r",
        encoding="utf-8",
    ) as f:
        # load the holding data
        holding = json.load(f)

        # filter out cex
        holding = {k: v for k, v in holding.items() if k not in cex_dex}

        # isolate the whales and non-whales
        all_holding = sum(holding.values())
        whale = set(k for k, v in holding.items() if v >= all_holding * WHALE_THRESHOLD)
        non_whale = set(
            k for k, v in holding.items() if v < all_holding * WHALE_THRESHOLD
        )

        if all_holding <= 0:
            return set(), set()

    return whale, non_whale


def identify_identity(
    df: pd.DataFrame,
    whale_lower_set: set,
    whale_upper_set: set,
    non_whale_lower_set: set,
    non_whale_upper_set: set,
    cex_dex_set: set,
    staking_set: set,
) -> None:
    """Function to identify the identity of the participants"""

    # identify the identity of the participants
    participants = set(df["from"]).union(set(df["to"]))
    participants_whale = participants.intersection(whale_lower_set).union(
        participants.intersection(whale_upper_set)
    )
    participants_non_whale = participants.intersection(non_whale_lower_set).union(
        participants.intersection(non_whale_upper_set)
    )
    participants_cex_dex = participants.intersection(cex_dex_set)
    participants_staking = participants.intersection(staking_set)
    other_participants = participants.difference(
        participants_whale.union(participants_non_whale)
        .union(participants_cex_dex)
        .union(participants_staking)
    )

    identities = {
        **{k: "whale" for k in participants_whale},
        **{k: "non_whale" for k in participants_non_whale},
        **{k: "cex_dex" for k in participants_cex_dex},
        **{k: "smart_contract" for k in participants_staking},
        **{k: "other" for k in other_participants},
    }
    df["identity_from"] = df["from"].map(identities)
    df["identity_to"] = df["to"].map(identities)


def intermediary_cluster(df: pd.DataFrame) -> list[pd.DataFrame]:
    """Function to cluster the intermediary nodes"""

    # isolate the intermediary "other" nodes and perform clustering
    df_other = df.loc[
        (df["identity_from"] == "other") | (df["identity_to"] == "other")
    ].reset_index(drop=True)

    # Start seeds: all rows with identity_to == "other"
    df_other_to = df_other.loc[
        (df_other["identity_from"] != "other") & (df_other["identity_to"] == "other")
    ].copy()

    # Expandable edges (everything else)
    remaining = df_other.loc[df_other.index.difference(df_other_to.index)].copy()

    clusters = []
    # Seed per unique `to` address (the "Other" node)
    for other_node, seed_rows in df_other_to.groupby("to"):
        # cluster starts with *all* rows that go into this `other_node`
        cluster_parts = [seed_rows.reset_index(drop=True)]

        # BFS frontier is the `other_node`
        frontier = {other_node}
        visited_to = set(frontier)

        while True:
            df_next = remaining[remaining["from"].isin(frontier)]
            if df_next.empty:
                break

            cluster_parts.append(df_next)

            new_to = set(df_next["to"].tolist())
            new_frontier = new_to - visited_to
            visited_to |= new_to

            # consume used rows once
            remaining = remaining.drop(df_next.index)

            frontier = new_frontier
            if not frontier:
                break

        clusters.append(pd.concat(cluster_parts, ignore_index=True))

    return [_ for _ in clusters if len(_) > 1]


def agg_router(g: pd.DataFrame, tol: float = 1) -> pd.DataFrame:
    """Function to aggregate the router transactions"""

    # aggregate the transfers between two nodes
    cap = defaultdict(lambda: defaultdict(float))
    for f, t, a in g[["from", "to", "amount"]].itertuples(index=False):
        cap[f][t] += float(a)

    # Node balances
    out_amt = defaultdict(float)
    in_amt = defaultdict(float)
    for u in cap:
        for v, a in cap[u].items():
            out_amt[u] += a
            in_amt[v] += a

    remaining_src = {n: out_amt[n] - in_amt[n] for n in set(out_amt) | set(in_amt)}
    sources = {n: v for n, v in remaining_src.items() if v > 0}
    sinks = {n: -v for n, v in remaining_src.items() if v < 0}

    if len(sources) == 1 and len(sinks) == 1:
        return pd.DataFrame(
            {
                "from": list(sources.keys()),
                "to": list(sinks.keys()),
                "amount": list(sources.values()),
            }
        )
    elif len(sources) == 1 and len(sinks) != 1:
        return pd.DataFrame(
            {
                "from": list(sources.keys()) * len(sinks),
                "to": list(sinks.keys()),
                "amount": list(sinks.values()),
            }
        )
    elif len(sources) != 1 and len(sinks) == 1:
        return pd.DataFrame(
            {
                "from": list(sources.keys()),
                "to": list(sinks.keys()) * len(sources),
                "amount": list(sources.values()),
            }
        )
    else:
        # proportional distribution
        total_src = sum(sources.values())
        total_sink = sum(sinks.values())
        if abs(total_src - total_sink) > tol:
            raise ValueError("Total source and sink amount do not match")

        flow = []
        for s, sa in sources.items():
            for t, ta in sinks.items():
                flow.append(
                    {
                        "from": s,
                        "to": t,
                        "amount": sa * (ta / total_sink),
                    }
                )
        return pd.DataFrame(flow)


if __name__ == "__main__":

    # load the proposal data with block and smart contract info
    df_proposals_adj = pd.read_csv(
        PROCESSED_DATA_DIR / "proposals_adjusted_with_sc_block.csv"
    )
    df_proposals_adj["scores"] = df_proposals_adj["scores"].apply(literal_eval)

    # load the cex and dex set
    with open(PROCESSED_DATA_DIR / "cex_dex.pkl", "rb") as f:
        cex_dex = pickle.load(f)

    flow = []

    for address, group in tqdm(
        df_proposals_adj.groupby("address"), total=df_proposals_adj["address"].nunique()
    ):
        # load the transfer data
        df_transfer = pd.read_csv(PROCESSED_DATA_DIR / "transfer" / f"{address}.csv")

        # load the contract data
        df_contract = pd.read_csv(PROCESSED_DATA_DIR / "contract" / f"{address}.csv")
        contract = set(df_contract["address"].to_list())
        staking = contract.difference(cex_dex)

        for _, proposal in group.iterrows():
            for stage in ["created", "end"]:
                # get the block range for the stage
                lower_block = proposal[f"{stage}_ts_-5d_block"]
                upper_block = proposal[f"{stage}_ts_+5d_block"]
                lower_price = proposal[f"{stage}_-5d_price"]
                upper_price = proposal[f"{stage}_+5d_price"]

                # get the transfer data in the block range
                df_stage = df_transfer.loc[
                    (df_transfer["blockNumber"] >= lower_block)
                    & (df_transfer["blockNumber"] < upper_block)
                ]
                if df_stage.empty:
                    continue

                # handle the router transactions
                df_stage_agg = []
                for txn_hash, g in df_stage.groupby("transactionHash"):
                    if len(g) >= 2:
                        df_router = agg_router(g)
                        df_stage_agg.append(df_router)
                    else:
                        df_stage_agg.append(g)
                df_stage = pd.concat(df_stage_agg, ignore_index=True)

                # load the lower block holding
                whale_lower, non_whale_lower = load_whale(address, lower_block, cex_dex)

                # load the upper block holding
                whale_upper, non_whale_upper = load_whale(address, upper_block, cex_dex)

                # identify the identity of the participants
                identify_identity(
                    df_stage,
                    whale_lower,
                    whale_upper,
                    non_whale_lower,
                    non_whale_upper,
                    cex_dex,
                    staking,
                )

                # isolate the intermediary "other" nodes and perform clustering
                df_other_cluster = intermediary_cluster(df_stage)
                df_stage = df_stage.loc[
                    (df_stage["identity_from"] != "other")
                    & (df_stage["identity_to"] != "other")
                ].reset_index(drop=True)

                for cluster in df_other_cluster:
                    df_cluster_agg = agg_router(cluster)
                    df_stage = pd.concat([df_stage, df_cluster_agg], ignore_index=True)

                # re-identify the identity of the participants
                identify_identity(
                    df_stage,
                    whale_lower,
                    whale_upper,
                    non_whale_lower,
                    non_whale_upper,
                    cex_dex,
                    staking,
                )

                # aggregate the transfer amount by identity
                df_stage_agg = (
                    df_stage.groupby(["identity_from", "identity_to"])["amount"]
                    .sum()
                    .reset_index()
                )
                df_stage_agg["proposal_id"] = proposal["id"]
                df_stage_agg["stage"] = stage

                flow.append(df_stage_agg)

    df_flow = pd.concat(flow, ignore_index=True)
    df_flow.to_csv(PROCESSED_DATA_DIR / "transfer_characteristics.csv", index=False)

    # pick the directed edges you care about
    EDGE_LIST = [
        ("cex_dex", "whale"),
        ("whale", "cex_dex"),
        ("cex_dex", "non_whale"),
        ("non_whale", "cex_dex"),
    ]
    edge_df = pd.DataFrame(EDGE_LIST, columns=["identity_from", "identity_to"])

    # Filter to just the edges of interest
    df_txn0 = df_flow.merge(edge_df, on=["identity_from", "identity_to"], how="inner")

    # Collapse duplicates just in case
    df_txn0 = (
        df_txn0.groupby(["proposal_id", "stage", "identity_from", "identity_to"])[
            "amount"
        ]
        .sum()
        .reset_index()
    )

    # cartesian-product to "complete the edge space" with zeros
    keys = df_txn0[["proposal_id", "stage"]].drop_duplicates()

    # cross join (works in pandas>=1.2 using merge with a dummy key)
    keys["key"] = 1
    edge_df["key"] = 1
    full = keys.merge(edge_df, on="key", how="outer").drop(columns="key")

    # left-join the actual amounts; fill missing with 0
    full = full.merge(
        df_txn0, on=["proposal_id", "stage", "identity_from", "identity_to"], how="left"
    ).fillna({"amount": 0.0})

    # compute per-(proposal, stage) totals and percentages (safe with zeros)
    full["amount_total"] = full.groupby(["proposal_id", "stage"])["amount"].transform(
        "sum"
    )
    # avoid division by zero: if a proposal-stage has no flow in your filtered edges, keep pct=0
    full["amount_pct"] = 0.0
    mask = full["amount_total"] > 0
    full.loc[mask, "amount_pct"] = (
        full.loc[mask, "amount"] / full.loc[mask, "amount_total"]
    )

    df_mean_unweighted = (
        full.groupby(["stage", "identity_from", "identity_to"])["amount_pct"]
        .mean()
        .reset_index()
    )
    df_mean_unweighted.to_csv(
        PROCESSED_DATA_DIR / "txn.csv",
        index=False,
    )
