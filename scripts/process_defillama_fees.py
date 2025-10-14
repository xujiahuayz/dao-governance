"""Script to merge and process defillama fee protocols"""

import json
import pandas as pd
from tqdm import tqdm

from governenv.constants import DATA_DIR, PROCESSED_DATA_DIR


# Get the mslug
defillama_fee_protocols = pd.read_csv(DATA_DIR / "defillama_fee_protocols.csv")
defillama_fee_protocols["mslug"] = defillama_fee_protocols.apply(
    lambda row: (
        row["slug"]
        if pd.isna(row["parentProtocol"])
        else row["parentProtocol"].split("#")[-1]
    ),
    axis=1,
)
defillama_fee_protocols = defillama_fee_protocols.loc[
    defillama_fee_protocols["category"] != "Chain"
]

# Merge the fee protocols
fees_panel = []

for index, row in tqdm(
    defillama_fee_protocols.iterrows(), total=len(defillama_fee_protocols)
):
    slug = row["slug"]
    mslug = row["mslug"]
    with open(
        DATA_DIR / "defillama" / "fees" / f"{slug}.json", "r", encoding="utf-8"
    ) as f:
        data = json.load(f)
    fees = data["totalDataChart"]
    df_fees = pd.DataFrame(
        {
            "date": [item[0] for item in fees],
            "fee": [item[1] for item in fees],
        }
    )
    df_fees["date"] = pd.to_datetime(df_fees["date"], unit="s")
    df_fees["slug"] = slug
    df_fees["mslug"] = mslug
    fees_panel.append(df_fees)

df_fees = pd.concat(fees_panel, ignore_index=True)
df_fees = df_fees.groupby(["date", "mslug"]).agg(fee=("fee", "sum")).reset_index()
df_fees = df_fees[df_fees["fee"] >= 0]
df_fees.to_csv(PROCESSED_DATA_DIR / "fees.csv", index=False)
