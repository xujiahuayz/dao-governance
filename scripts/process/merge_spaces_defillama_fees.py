"""Merge spaces data with DefiLlama fee protocols list."""

import gzip
import json

import pandas as pd

from governenv.constants import SNAPSHOT_PATH, DATA_DIR, PROCESSED_DATA_DIR
from governenv.utils import clean_name, match_top

# load the data
with gzip.open(SNAPSHOT_PATH, "rt") as f:
    # load data and skip duplicates
    spaces = [json.loads(line) for line in f]

# keep proposal number > 0 and verified
spaces = [item for item in spaces if (item["proposalsCount"] > 0) & item["verified"]]
df_spaces = pd.DataFrame(spaces).rename(
    columns={"id": "space_id", "name": "space_name"}
)[["space_id", "space_name", "coingecko"]]
df_spaces["cname"] = df_spaces["space_name"].apply(clean_name)

# defillama fee protocols
defillama_fee_protocols = pd.read_csv(DATA_DIR / "defillama_fee_protocols.csv")
defillama_fee_protocols["mslug"] = defillama_fee_protocols.apply(
    lambda row: (
        row["slug"]
        if pd.isna(row["parentProtocol"])
        else row["parentProtocol"].split("#")[-1]
    ),
    axis=1,
)
defillama_fee_protocols = defillama_fee_protocols[["slug", "mslug"]]
defillama_fee_protocols["cname"] = defillama_fee_protocols["mslug"].apply(clean_name)
candidates = set(defillama_fee_protocols["cname"].tolist())

# merge with fee protocols
df_spaces["match"] = df_spaces["cname"].apply(
    lambda x: match_top(x, candidates, n=3, method="jaro_win")
)
df_spaces["match1"], df_spaces["match2"], df_spaces["match3"] = zip(
    *list(df_spaces["match"].values)
)
for i in range(3):
    i += 1
    df_spaces[f"score{i}"], df_spaces[f"m_namec{i}"] = zip(
        *list(df_spaces[f"match{i}"].values)
    )

df_spaces = df_spaces[
    [
        "space_id",
        "space_name",
        "cname",
        "score1",
        "m_namec1",
    ]
]

# manual corrections
cname_space_defillama = {
    "gnosisdao": "gnosis",
    "juiceboxdao": "juicebox",
    "safedao": "safe",
    "baby doge": "babydogecoin",
}

for k, v in cname_space_defillama.items():
    df_spaces.loc[df_spaces["cname"] == k, "m_namec1"] = v
    df_spaces.loc[df_spaces["cname"] == k, "score1"] = 1.0

df_spaces = df_spaces.loc[df_spaces["score1"] == 1.0].drop(
    ["score1", "m_namec1"], axis=1
)
df_spaces = (
    df_spaces.groupby("cname")
    .agg(
        space_id=("space_id", list),
        space_name=("space_name", list),
    )
    .reset_index()
)
df_spaces = df_spaces.merge(
    defillama_fee_protocols[["cname", "slug"]],
    on="cname",
    how="left",
)
df_spaces.dropna(subset=["slug"], inplace=True)
df_spaces = (
    df_spaces.groupby("cname")
    .agg(
        space_id=("space_id", "first"),
        space_name=("space_name", "first"),
        slug=("slug", list),
    )
    .reset_index()
)

df_spaces.rename(columns={"cname": "mslug"}, inplace=True)

# save the processed spaces data
df_spaces.to_csv(PROCESSED_DATA_DIR / "spaces_defillama_fees.csv", index=False)
