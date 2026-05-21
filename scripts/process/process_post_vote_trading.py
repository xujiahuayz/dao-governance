"""Analyze post-vote trading by small shareholders.

The analysis focuses on exchange-mediated governance-token trading around the
vote-end event window, matching the end-stage Sankey window. A small shareholder
is counted as buying when their wallet receives the token from a known CEX/DEX
address, and selling when their wallet sends the token to a known CEX/DEX address.
"""

from __future__ import annotations

import argparse
from ast import literal_eval
from multiprocessing import Pool
from pathlib import Path
import pickle
import sys

import numpy as np
import pandas as pd
from tqdm import tqdm

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from governenv.constants import FIGURE_DIR, PROCESSED_DATA_DIR


VICTORY_COLUMNS = [
    "non_whale_victory_vp",
    "non_whale_victory_vn",
    "non_whale_victory_vp_vn",
]

WORKER_SMALL_VOTES = None
WORKER_CEX_DEX = None
WORKER_START_BLOCK_COL = None
WORKER_END_BLOCK_COL = None


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments."""

    parser = argparse.ArgumentParser(
        description=(
            "Estimate the likelihood of end-event-window buying/selling by small "
            "shareholders conditional on voting outcomes."
        )
    )
    parser.add_argument(
        "--victory-metric",
        choices=VICTORY_COLUMNS,
        default="non_whale_victory_vp",
        help="Small-shareholder victory definition used for win/loss splits.",
    )
    parser.add_argument(
        "--start-block-col",
        default="end_ts_-5d_block",
        help="Proposal column used as the start of the end-event trading window.",
    )
    parser.add_argument(
        "--end-block-col",
        default="end_ts_+5d_block",
        help="Proposal column used as the end of the end-event trading window.",
    )
    parser.add_argument(
        "--output-prefix",
        default="post_vote_trading",
        help="Prefix for output CSV files in processed_data.",
    )
    parser.add_argument(
        "--no-sankey",
        action="store_true",
        help="Skip conditional Sankey figure outputs.",
    )
    parser.add_argument(
        "--processes",
        type=int,
        default=1,
        help="Number of worker processes for proposal-level transfer scanning.",
    )
    return parser.parse_args()


def require_columns(df: pd.DataFrame, columns: list[str], name: str) -> None:
    """Raise a clear error if an input file is missing required columns."""

    missing = sorted(set(columns) - set(df.columns))
    if missing:
        raise ValueError(f"{name} is missing required columns: {missing}")


def parse_maybe_literal(value):
    """Parse a Python-literal string when possible, otherwise return as-is."""

    if not isinstance(value, str):
        return value
    try:
        return literal_eval(value)
    except (ValueError, SyntaxError):
        return value


def normalize_choice(value) -> str:
    """Normalize Snapshot choices so they can be compared to winning choice ids."""

    if isinstance(value, float) and np.isnan(value):
        return ""
    if isinstance(value, float) and value.is_integer():
        return str(int(value))
    return str(value)


def winning_choice(row: pd.Series) -> str:
    """Return the Snapshot winning choice id for a proposal."""

    scores = row["scores"]
    if not scores:
        return ""

    ranked = sorted(
        zip([str(idx + 1) for idx, _ in enumerate(row["choices"])], scores),
        key=lambda item: item[1],
        reverse=True,
    )
    return ranked[0][0]


def process_vote_like_process_voter(df: pd.DataFrame) -> pd.DataFrame:
    """Apply the same choice expansion logic used in process_voter.py."""

    df_list = []
    df = df.copy()
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


def process_votes_by_proposal(df_votes: pd.DataFrame) -> pd.DataFrame:
    """Process choices with the same proposal-level rule as process_voter.py."""

    processed = []
    for _, subset in df_votes.groupby("proposal_id"):
        subset = subset.copy()
        if len(subset["type"].unique()) == 1:
            subset = process_vote_like_process_voter(subset)
        subset["choice"] = subset["choice"].apply(normalize_choice)
        processed.append(subset)

    return pd.concat(processed, ignore_index=True) if processed else pd.DataFrame()


def load_inputs(args: argparse.Namespace) -> tuple[pd.DataFrame, pd.DataFrame, set[str]]:
    """Load and validate proposal, voter, and CEX/DEX data."""

    proposals = pd.read_csv(PROCESSED_DATA_DIR / "proposals_with_sc_blocks.csv")
    for col in ["address", "choices", "scores"]:
        proposals[col] = proposals[col].apply(parse_maybe_literal)
    require_columns(
        proposals,
        ["id", "address", "choices", "scores", args.start_block_col, args.end_block_col],
        "proposals_with_sc_blocks.csv",
    )
    proposals["win_choice"] = proposals.apply(winning_choice, axis=1)

    voter = pd.read_csv(PROCESSED_DATA_DIR / "proposals_voter.csv")
    require_columns(voter, ["id", args.victory_metric], "proposals_voter.csv")
    proposals = proposals.merge(voter[["id", args.victory_metric]], on="id", how="left")

    voter_label = pd.read_csv(PROCESSED_DATA_DIR / "proposal_voter_label.csv")
    require_columns(voter_label, ["id", "voter", "label"], "proposal_voter_label.csv")
    voter_label = voter_label.loc[voter_label["label"] == "non_whales"].copy()
    voter_label["voter"] = voter_label["voter"].str.lower()

    votes = pd.read_csv(PROCESSED_DATA_DIR / "votes.csv")
    require_columns(votes, ["proposal_id", "voter", "choice", "type", "vp"], "votes.csv")
    votes["voter"] = votes["voter"].str.lower()
    votes = process_votes_by_proposal(votes)

    small_votes = voter_label.merge(
        votes[["proposal_id", "voter", "choice", "vp"]],
        left_on=["id", "voter"],
        right_on=["proposal_id", "voter"],
        how="left",
    ).drop(columns=["proposal_id"])
    small_votes = small_votes.merge(
        proposals[["id", "win_choice", args.victory_metric]],
        on="id",
        how="left",
    )
    small_votes["against_vp"] = np.where(
        small_votes["choice"].notna()
        & small_votes["win_choice"].ne("")
        & (small_votes["choice"] != small_votes["win_choice"]),
        small_votes["vp"].fillna(0),
        0.0,
    )
    small_votes["vp"] = small_votes["vp"].fillna(0.0)
    small_votes = (
        small_votes.groupby(["id", "voter", "label", "win_choice", args.victory_metric])
        .agg(vp=("vp", "sum"), against_vp=("against_vp", "sum"))
        .reset_index()
    )
    small_votes["vote_against_outcome"] = (
        small_votes["vp"].gt(0) & small_votes["against_vp"].gt(small_votes["vp"] / 2)
    )

    with open(PROCESSED_DATA_DIR / "cex_dex.pkl", "rb") as f:
        cex_dex = {addr.lower() for addr in pickle.load(f)}

    return proposals, small_votes, cex_dex


def proposal_trade_flags(
    proposal: pd.Series,
    small_votes: pd.DataFrame,
    cex_dex: set[str],
    start_block_col: str,
    end_block_col: str,
) -> pd.DataFrame:
    """Calculate end-event-window buy/sell flags for small voters in one proposal."""

    proposal_id = proposal["id"]
    voters = small_votes.loc[small_votes["id"] == proposal_id].copy()
    if voters.empty:
        return pd.DataFrame()

    start_block = proposal[start_block_col]
    end_block = proposal[end_block_col]
    if pd.isna(start_block) or pd.isna(end_block) or start_block >= end_block:
        voters["buy_amount"] = 0.0
        voters["sell_amount"] = 0.0
        return voters

    buy_amount = pd.Series(0.0, index=voters["voter"])
    sell_amount = pd.Series(0.0, index=voters["voter"])
    voter_set = set(voters["voter"])

    for token in proposal["address"]:
        token_address = token["address"].lower()
        transfer_path = PROCESSED_DATA_DIR / "transfer" / f"{token_address}.csv"
        if not transfer_path.exists():
            continue

        transfers = pd.read_csv(
            transfer_path,
            usecols=["blockNumber", "from", "to", "amount"],
        )
        transfers["from"] = transfers["from"].str.lower()
        transfers["to"] = transfers["to"].str.lower()
        window = transfers.loc[
            (transfers["blockNumber"] >= start_block)
            & (transfers["blockNumber"] < end_block)
        ]
        if window.empty:
            continue

        buys = window.loc[window["from"].isin(cex_dex) & window["to"].isin(voter_set)]
        sells = window.loc[window["from"].isin(voter_set) & window["to"].isin(cex_dex)]
        if not buys.empty:
            buy_amount = buy_amount.add(buys.groupby("to")["amount"].sum(), fill_value=0)
        if not sells.empty:
            sell_amount = sell_amount.add(
                sells.groupby("from")["amount"].sum(), fill_value=0
            )

    voters["buy_amount"] = voters["voter"].map(buy_amount).fillna(0.0)
    voters["sell_amount"] = voters["voter"].map(sell_amount).fillna(0.0)
    return voters


def init_worker(
    small_votes: pd.DataFrame,
    cex_dex: set[str],
    start_block_col: str,
    end_block_col: str,
) -> None:
    """Initialize read-only worker globals for multiprocessing."""

    global WORKER_SMALL_VOTES
    global WORKER_CEX_DEX
    global WORKER_START_BLOCK_COL
    global WORKER_END_BLOCK_COL

    WORKER_SMALL_VOTES = small_votes
    WORKER_CEX_DEX = cex_dex
    WORKER_START_BLOCK_COL = start_block_col
    WORKER_END_BLOCK_COL = end_block_col


def proposal_trade_flags_worker(proposal: pd.Series) -> pd.DataFrame:
    """Worker wrapper using process-global static inputs."""

    return proposal_trade_flags(
        proposal,
        WORKER_SMALL_VOTES,
        WORKER_CEX_DEX,
        WORKER_START_BLOCK_COL,
        WORKER_END_BLOCK_COL,
    )


def build_wallet_records(
    proposals: pd.DataFrame,
    small_votes: pd.DataFrame,
    cex_dex: set[str],
    start_block_col: str,
    end_block_col: str,
    processes: int,
) -> list[pd.DataFrame]:
    """Build proposal-wallet trading records, optionally in parallel."""

    proposal_rows = [row for _, row in proposals.iterrows()]
    if processes <= 1:
        return [
            proposal_trade_flags(
                proposal, small_votes, cex_dex, start_block_col, end_block_col
            )
            for proposal in tqdm(proposal_rows, desc="End-event trading")
        ]

    with Pool(
        processes=processes,
        initializer=init_worker,
        initargs=(small_votes, cex_dex, start_block_col, end_block_col),
    ) as pool:
        return list(
            tqdm(
                pool.imap_unordered(proposal_trade_flags_worker, proposal_rows),
                total=len(proposal_rows),
                desc=f"End-event trading ({processes} processes)",
            )
        )


def summarize_condition(
    wallet: pd.DataFrame,
    mask: pd.Series,
    condition: str,
) -> dict[str, float | int | str]:
    """Summarize wallet- and proposal-level trading likelihood for one condition."""

    subset = wallet.loc[mask].copy()
    if subset.empty:
        return {
            "condition": condition,
            "proposal_n": 0,
            "wallet_n": 0,
            "buy_wallet_prob": np.nan,
            "sell_wallet_prob": np.nan,
            "trade_wallet_prob": np.nan,
            "any_buy_proposal_prob": np.nan,
            "any_sell_proposal_prob": np.nan,
            "buy_amount_per_wallet": np.nan,
            "sell_amount_per_wallet": np.nan,
        }

    proposal = subset.groupby("id").agg(
        any_buy=("bought", "max"),
        any_sell=("sold", "max"),
    )
    return {
        "condition": condition,
        "proposal_n": int(subset["id"].nunique()),
        "wallet_n": int(len(subset)),
        "buy_wallet_prob": subset["bought"].mean(),
        "sell_wallet_prob": subset["sold"].mean(),
        "trade_wallet_prob": subset["traded"].mean(),
        "any_buy_proposal_prob": proposal["any_buy"].mean(),
        "any_sell_proposal_prob": proposal["any_sell"].mean(),
        "buy_amount_per_wallet": subset["buy_amount"].mean(),
        "sell_amount_per_wallet": subset["sell_amount"].mean(),
    }


def write_sankey_figures(summary: pd.DataFrame, output_prefix: str) -> None:
    """Write conditional post-vote buy/sell Sankey figures."""

    try:
        import plotly.graph_objects as go
    except ImportError as exc:
        print(f"Skipping Sankey figures because plotly is not installed: {exc}")
        return

    FIGURE_DIR.mkdir(parents=True, exist_ok=True)
    display_name = {
        "small_shareholder_victory": "Small Shareholder Victory",
        "small_shareholder_loss": "Small Shareholder Loss",
        "small_vote_against_outcome": "Small Vote Against Outcome",
    }

    for _, row in summary.iterrows():
        condition = row["condition"]
        buy_prob = 0.0 if pd.isna(row["buy_wallet_prob"]) else row["buy_wallet_prob"]
        sell_prob = 0.0 if pd.isna(row["sell_wallet_prob"]) else row["sell_wallet_prob"]

        fig = go.Figure(
            data=[
                go.Sankey(
                    arrangement="fixed",
                    node=dict(
                        pad=20,
                        thickness=20,
                        line=dict(color="black", width=0.5),
                        label=[
                            "CEXs and DEXs",
                            "Small Shareholders",
                            "Small Shareholders",
                            "CEXs and DEXs",
                        ],
                        color=["#ffcc00", "#1f77b4", "#1f77b4", "#ffcc00"],
                        x=[0.08, 0.92, 0.08, 0.92],
                        y=[0.15, 0.15, 0.85, 0.85],
                    ),
                    link=dict(
                        source=[0, 2],
                        target=[1, 3],
                        value=[buy_prob, sell_prob],
                        label=[
                            f"Buy: {buy_prob * 100:.1f}%",
                            f"Sell: {sell_prob * 100:.1f}%",
                        ],
                        hovertemplate="%{label}<extra></extra>",
                        color=["rgba(31,119,180,0.35)", "rgba(255,127,14,0.35)"],
                    ),
                )
            ]
        )
        fig.update_layout(
            title=dict(
                text=(
                    f"{display_name.get(condition, condition)} "
                    f"(wallets={int(row['wallet_n'])}, proposals={int(row['proposal_n'])})"
                ),
                x=0.5,
            ),
            annotations=[
                dict(
                    x=0.5,
                    y=0.68,
                    xref="paper",
                    yref="paper",
                    text=f"Buy: {buy_prob * 100:.1f}%",
                    showarrow=False,
                    font=dict(size=16, color="black"),
                ),
                dict(
                    x=0.5,
                    y=0.32,
                    xref="paper",
                    yref="paper",
                    text=f"Sell: {sell_prob * 100:.1f}%",
                    showarrow=False,
                    font=dict(size=16, color="black"),
                ),
            ],
            font=dict(size=16, color="black"),
            autosize=False,
            width=800,
            height=500,
        )

        stem = f"sankey_{output_prefix}_{condition}"
        html_path = FIGURE_DIR / f"{stem}.html"
        pdf_path = FIGURE_DIR / f"{stem}.pdf"
        fig.write_html(html_path)
        try:
            fig.write_image(pdf_path, format="pdf", width=800, height=500, scale=3)
        except Exception as exc:
            print(f"Could not write {pdf_path}: {exc}")
        print(f"Wrote {html_path}")


def main() -> None:
    """Run the end-event-window small-shareholder trading analysis."""

    args = parse_args()
    proposals, small_votes, cex_dex = load_inputs(args)

    processes = max(1, args.processes)
    records = build_wallet_records(
        proposals,
        small_votes,
        cex_dex,
        args.start_block_col,
        args.end_block_col,
        processes,
    )

    records = [record for record in records if not record.empty]
    if not records:
        raise ValueError("No small-shareholder proposal-wallet records were generated.")

    wallet = pd.concat(records, ignore_index=True)
    wallet["bought"] = wallet["buy_amount"].gt(0).astype(int)
    wallet["sold"] = wallet["sell_amount"].gt(0).astype(int)
    wallet["traded"] = wallet[["bought", "sold"]].max(axis=1)
    wallet["small_victory"] = wallet[args.victory_metric]
    wallet["vote_against_outcome"] = wallet["vote_against_outcome"].astype(int)

    victory = wallet[args.victory_metric].eq(1)
    loss = wallet[args.victory_metric].eq(0)
    against = wallet["vote_against_outcome"].eq(1)
    summary = pd.DataFrame(
        [
            summarize_condition(wallet, victory, "small_shareholder_victory"),
            summarize_condition(wallet, loss, "small_shareholder_loss"),
            summarize_condition(wallet, against, "small_vote_against_outcome"),
        ]
    )

    wallet_out = PROCESSED_DATA_DIR / f"{args.output_prefix}_wallet.csv"
    summary_out = PROCESSED_DATA_DIR / f"{args.output_prefix}_summary.csv"
    wallet.to_csv(wallet_out, index=False)
    summary.to_csv(summary_out, index=False)

    if not args.no_sankey:
        write_sankey_figures(summary, args.output_prefix)

    print(f"Wrote {wallet_out}")
    print(f"Wrote {summary_out}")
    print(summary.to_string(index=False))


if __name__ == "__main__":
    main()
