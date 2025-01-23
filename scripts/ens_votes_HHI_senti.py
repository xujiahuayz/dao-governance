"""
combine ens_vp.json, ens_hhi.json and ens_senti.json into a single CSV file
"""

import json
import pandas as pd
from datetime import datetime
from governenv.constants import DATA_DIR

# Load and process `ens_senti.json` file
with open(DATA_DIR / "ens_senti.json", "r") as f:
    senti_json = json.load(f)

tidied_json = [
    {"discussion": url, **details["class_prob"]} for url, details in senti_json.items()
]

# Load the two JSON files (ens_hhi.json and ens_vp.json)
with open(DATA_DIR / "ens_vp.json", "r") as f:
    data_vp = json.load(f)

with open(DATA_DIR / "ens_hhi.json", "r") as f:
    data_hhi = json.load(f)

# Convert JSON to Pandas df
df_vp = pd.DataFrame(data_vp)
df_hhi = pd.DataFrame(data_hhi)
df_senti = pd.DataFrame(tidied_json)

# Merge the three dataframes
df = pd.merge(df_vp, df_hhi, on="id", how="outer")
df = pd.merge(df, df_senti, on="discussion", how="outer")


df.drop(columns=["url"], inplace=True)

df["half_vp_sum_time"] = pd.to_numeric(df["half_vp_sum_time"], errors="coerce").astype(
    "Int64"
)  # Convert float to integer

# Add a new column 'UTC time' to convert 'half_vp_sum_time' to UTC time
df["UTC time"] = df["half_vp_sum_time"].apply(
    lambda x: datetime.utcfromtimestamp(int(x)) if pd.notnull(x) else None
)  # Convert timestamp to UTC time

df["half_voters_count"] = pd.to_numeric(
    df["half_voters_count"], errors="coerce"
).astype(
    "Int64"
)  # Convert float to integer

df["number_of_discussions"] = pd.to_numeric(
    df["number_of_discussions"], errors="coerce"
).astype(
    "Int64"
)  # Convert float to integer

# Reorder columns
columns_order = [col for col in df.columns]
columns_order.insert(6, columns_order.pop(-1))
df = df[columns_order]

# Rename columns
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

# Save the df to a CSV file
with open(DATA_DIR / "ens_summary.csv", "w") as f:
    df.to_csv(f, index=False)
