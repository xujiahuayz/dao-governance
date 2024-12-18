"""
Calculate the HHI for each url to evaluate the concentration of activity:
"""

import json
from governenv.constants import DATA_DIR
from collections import defaultdict

output = []

with open(DATA_DIR / "ens_authors.json", "r") as f:
    data = json.load(f)


for entry in data:
    id = entry["id"]
    url = entry["discussion_url"]
    discussions = entry["discussion"]

    authors_count = defaultdict(int)
    content_group_authors = defaultdict(int)
    total_len=0

    for post in discussions:
        author = post["author"]
        authors_count[author] += 1 # Count the number of discussions each author posted
        content_individual = len(post["content"])
        content_group_authors[author] += content_individual # Count the total length of content each author posted
        total_len += content_individual # Count the toal length of content in the whole discussion thread


    # Calculate the lenth of discussions HHI
    HHI_len = sum(value**2 for value in content_group_authors.values())
    if total_len > 0:
        HHI_len_normalised = HHI_len / (total_len**2)
    else:
        HHI_len_normalised = None


    # Calculate equal weight HHI 
    HHI_eq = sum(value**2 for value in authors_count.values())
    if len(discussions) > 0:
        HHI_eq_normalised = HHI_eq / (len(discussions)**2)
    else:
        HHI_eq_normalised = None

    output.append(
        {
            "id": id,
            "url": url,
            "number_of_discussions": len(discussions),
            "HHI_length_weighted": HHI_len_normalised,
            "HHI_equal_weighted": HHI_eq_normalised,
        }
    )

with open(DATA_DIR / "ens_hhi.json", "w") as file:
    json.dump(output, file, indent=4)
