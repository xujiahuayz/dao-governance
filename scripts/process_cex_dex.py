"""Script to process the cex and dex labels"""

import pickle

import pandas as pd

from governenv.constants import DATA_DIR, PROCESSED_DATA_DIR

df_label = pd.read_csv(DATA_DIR / "label_flipside.csv")

cex_dex_set = set(
    df_label.loc[
        (df_label["LABEL_SUBTYPE"] == "pool")
        | (
            (df_label["LABEL_TYPE"] == "cex")
            & (
                (df_label["LABEL_SUBTYPE"] == "hot_wallet")
                | (df_label["LABEL_SUBTYPE"] == "deposit_wallet")
            )
        ),
        "ADDRESS",
    ].to_list()
)

with open(PROCESSED_DATA_DIR / "cex_dex.pkl", "wb") as f:
    pickle.dump(cex_dex_set, f)
