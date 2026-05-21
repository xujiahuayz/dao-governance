"""Build the regression panel for post-vote/end-event small-shareholder trading."""

from pathlib import Path
import sys

import numpy as np
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from governenv.constants import PROCESSED_DATA_DIR


TRADING_COLUMNS = [
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
    "small_victory",
]

PANEL_COLUMNS = [
    "id",
    "date",
    "gecko_id",
    "space",
    "topic",
    "multi_choices",
    "weighted",
    "ranked_choice",
    "quorum",
    "delegation",
    "have_discussion",
    "concensus",
    "professionalism",
]


def require_columns(df: pd.DataFrame, columns: list[str], name: str) -> None:
    """Raise a clear error if an input file is missing required columns."""

    missing = sorted(set(columns) - set(df.columns))
    if missing:
        raise ValueError(f"{name} is missing required columns: {missing}")


def main() -> None:
    """Merge wallet-level trading outcomes with proposal-level controls."""

    trading = pd.read_csv(PROCESSED_DATA_DIR / "post_vote_trading_wallet.csv")
    panel = pd.read_csv(PROCESSED_DATA_DIR / "proposals_panel.csv")

    require_columns(trading, TRADING_COLUMNS, "post_vote_trading_wallet.csv")
    require_columns(panel, PANEL_COLUMNS, "proposals_panel.csv")

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
