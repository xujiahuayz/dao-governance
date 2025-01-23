"""
combine the result from ens_vp.json, ens_hhi.json and ens_senti.json into a single CSV file
"""

import json
import pandas as pd
from governenv.constants import DATA_DIR

with open(DATA_DIR / "ens_senti.json", "r") as f:
    senti_json = json.load(f)
with open(DATA_DIR / "ens_vp.json", "r") as f:
    data_vp = json.load(f)
with open(DATA_DIR / "ens_hhi.json", "r") as f:
    data_hhi = json.load(f)

tidied_json = [
    {"discussion": url, **details["class_prob"]} for url, details in senti_json.items()
]

df_vp = pd.DataFrame(data_vp)
df_hhi = pd.DataFrame(data_hhi)
df_senti = pd.DataFrame(tidied_json)

df = pd.merge(
    pd.merge(df_vp, df_hhi, on="id", how="outer"),
    df_senti,
    on="discussion",
    how="outer",
)
df.drop(columns=["url"], inplace=True)

for col in ["half_vp_sum_time", "half_voters_count", "number_of_discussions"]:
    df[col] = pd.to_numeric(df[col], errors="coerce").astype("Int64")

df.rename(
    columns={
        "number": "total number of votes",
        "vp_sum": "sum of all voting power",
        "half_vp_sum_time": "timestamp when it reaches half of the voting power",
        "half_voters_count": "number of voters at half of the voting power",
        "number_of_discussions": "number of discussions",
        "HHI_length_weighted": "HHI length weighted",
        "HHI_equal_weighted": "HHI equal weighted",
    },
    inplace=True,
)

with open(DATA_DIR / "ens_summary.csv", "w") as f:
    df.to_csv(f, index=False)
