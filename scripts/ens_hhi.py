"""
Calculate the HHI for each url to evaluate the concentration of activity:
"""

import json
from governenv.constants import DATA_DIR

output = []

with open(DATA_DIR / "ens_authors.json", "r") as f:
    data = json.load(f)


for entry in data:
    id = entry["id"]
    url = entry["discussion_url"]
    discussions = entry["discussion"]

    content_lengths = [len(post["content"]) for post in discussions]
    total_len = sum(content_lengths)

    # Calculate the normalised lenth of discussions HHI
    HHI_len = sum(length**2 for length in content_lengths)
    if total_len > 0:
        HHI_len_normalised = HHI_len / (total_len**2)
    else:
        HHI_len_normalised = "null"

    # Calculate equal weighed HHI 
    if len(discussions) > 0:
        HHI_eq = 1 / len(discussions)
    else:
        HHI_eq = "null"

    output.append(
        {
            "id": id,
            "url": url,
            "number_of_discussions": len(discussions),
            "HHI_length_weighted": HHI_len_normalised,
            "HHI_equal_weighted": HHI_eq,
        }
    )

with open(DATA_DIR / "ens_hhi.json", "w") as file:
    json.dump(output, file, indent=4)
