"""Build the regression panel for end-event small-shareholder trading."""

from pathlib import Path
import sys

import numpy as np
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from governenv.constants import CRITERIA, PROCESSED_DATA_DIR, TOPICS


BASE_TRADING_COLUMNS = [
    "id",
    "voter",
    "vp",
    "against_vp",
    "vote_against_outcome",
    "buy_amount",
    "sell_amount",
    "bought",
    "sold",
    "traded",
]
VICTORY_COLUMNS = [
    "non_whale_victory_vp",
    "non_whale_victory_vn",
    "non_whale_victory_vp_vn",
]
TRADING_COLUMNS = BASE_TRADING_COLUMNS + ["small_victory"] + VICTORY_COLUMNS

PROPOSALS_CHAR = [
    "n_choices",
    "multi_choices",
    "duration",
    "quadratic",
    "weighted",
    "ranked_choice",
    "quorum",
    "delegation",
    "have_discussion",
]
TOPIC_COLUMNS = [topic.replace(" ", "_") for topic in TOPICS]
DISCUSSION_CHAR = [
    *[_.lower().replace(" ", "_") for _ in CRITERIA],
    "reply_number",
    "view_number",
    "like_number",
    "post_number",
    "hhi_post_number",
    "hhi_word_count",
]
PANEL_COLUMNS = [
    "id",
    "space",
    "gecko_id",
    "date",
    "topic",
    *PROPOSALS_CHAR,
    *TOPIC_COLUMNS,
    *DISCUSSION_CHAR,
]


def require_columns(df: pd.DataFrame, columns: list[str], name: str) -> None:
    """Raise a clear error if an input file is missing required columns."""

    missing = sorted(set(columns) - set(df.columns))
    if missing:
        raise ValueError(f"{name} is missing required columns: {missing}")


def build_proposal_panel() -> pd.DataFrame:
    """Build proposal controls with id, matching reg_small.py inputs."""

    proposals = pd.read_csv(PROCESSED_DATA_DIR / "proposals_with_sc_blocks.csv")
    require_columns(
        proposals,
        ["id", "space", "gecko_id", "created", "quorum", "have_discussion", "delegation"],
        "proposals_with_sc_blocks.csv",
    )
    proposals = proposals.drop(columns=["quorum", "have_discussion", "delegation"])

    proposals_char = pd.read_csv(PROCESSED_DATA_DIR / "proposals_char.csv")[
        ["id"] + PROPOSALS_CHAR
    ]
    proposals_topic = pd.read_csv(PROCESSED_DATA_DIR / "proposals_topic.csv")[
        ["id"] + TOPIC_COLUMNS
    ]
    proposals_discussion = pd.read_csv(
        PROCESSED_DATA_DIR / "proposals_discussion_char.csv"
    )[["id"] + DISCUSSION_CHAR]

    for df in [proposals_char, proposals_topic, proposals_discussion]:
        proposals = proposals.merge(df, on="id", how="left")

    proposals["date"] = pd.to_datetime(proposals["created"])
    proposals["have_discussion"] = proposals["have_discussion"].fillna(0).astype(int)
    proposals["topic"] = proposals[TOPIC_COLUMNS].idxmax(axis=1)

    return proposals[PANEL_COLUMNS]


def add_victory_columns(trading: pd.DataFrame) -> pd.DataFrame:
    """Add all small-shareholder victory definitions without rerunning trading."""

    voter = pd.read_csv(PROCESSED_DATA_DIR / "proposals_voter.csv")
    require_columns(voter, ["id"] + VICTORY_COLUMNS, "proposals_voter.csv")

    drop_cols = [col for col in VICTORY_COLUMNS if col in trading.columns]
    trading = trading.drop(columns=drop_cols)
    trading = trading.merge(voter[["id"] + VICTORY_COLUMNS], on="id", how="left")

    if "small_victory" not in trading.columns:
        trading["small_victory"] = trading["non_whale_victory_vp"]

    return trading


def main() -> None:
    """Merge wallet-level trading outcomes with proposal-level controls."""

    trading = pd.read_csv(PROCESSED_DATA_DIR / "post_vote_trading_wallet.csv")
    trading = add_victory_columns(trading)
    panel = build_proposal_panel()

    require_columns(
        trading,
        BASE_TRADING_COLUMNS + ["small_victory"] + VICTORY_COLUMNS,
        "post_vote_trading_wallet.csv",
    )
    require_columns(panel, PANEL_COLUMNS, "proposal controls")

    out = trading[TRADING_COLUMNS].merge(
        panel[PANEL_COLUMNS],
        on="id",
        how="inner",
        validate="many_to_one",
    )
    out["against_outcome"] = out["vote_against_outcome"]
    out["log_vp"] = np.log(out["vp"] + 1)

    out_path = PROCESSED_DATA_DIR / "post_vote_trading_panel.csv"
    out.to_csv(out_path, index=False)
    print(f"Wrote {out_path} ({len(out):,} rows)")


if __name__ == "__main__":
    main()
