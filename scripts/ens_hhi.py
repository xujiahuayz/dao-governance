"""
Calculate the HHI for each url to evaluate the concentration of activity:
"""

import json
import pandas as pd
from governenv.constants import DATA_DIR

output = []

with open(DATA_DIR / "ens_authors.json", "r") as f:
    data = json.load(f)

for entry in data:
    id = entry["id"]
    url = entry["discussion_url"]
    discussions = entry["discussion"]

    if not discussions:
        output.append(
            {
                "id": id,
                "url": url,
                "number_of_discussions": 0,
                "HHI_length_weighted": None,
                "HHI_equal_weighted": None,
            }
        )
        continue

    df = pd.DataFrame(discussions)
    df["content_length"] = df["content"].str.len()

    author_grouped = df.groupby("author")["content_length"].agg(["sum", "size"])

    total_len = df["content_length"].sum()
    HHI_len_normalised = (
        (author_grouped["sum"]**2).sum() / (total_len**2) if total_len > 0 else None
    )
    HHI_eq_normalised = (
        (author_grouped["size"]**2).sum() / (len(discussions)**2) if len(discussions) > 0 else None
    )

    output.append(
        {
            "id": id,
            "url": url,
            "number_of_discussions": len(discussions),
            "HHI_length_weighted": HHI_len_normalised,
            "HHI_equal_weighted": HHI_eq_normalised,
        }
    )

with open(DATA_DIR / "ens_hhi_df.json", "w") as file:
    json.dump(output, file, indent=4)

