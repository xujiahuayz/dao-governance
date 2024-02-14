import gzip
import json

import matplotlib.pyplot as plt
import pandas as pd

from governenv.constants import SNAPSHOT_PATH

# load the data


with gzip.open(SNAPSHOT_PATH, "rt") as f:
    # load data and skip duplicates
    data = [json.loads(line) for line in f]

# remove duplicates

data_unique = [
    json.loads(line) for line in set([json.dumps(row, sort_keys=True) for row in data])
]

# extract id, created, rank, proposalsCount, proposalsCount7d from each item in the list and make dataframe
# specify type of each column as str, int, int, int, int

df = pd.DataFrame(
    [
        {
            "id": item["id"],
            "created": int(item["created"]),
            "rank": item["rank"],
            "proposalsCount": item["proposalsCount"],
            "proposalsCount7d": item["proposalsCount7d"],
        }
        for item in data_unique
    ]
)

# sort by rank and remove those with no proposalsCount
df = df.sort_values(by="rank")
df = df[df["proposalsCount"] >= 1]

# plot the distribution of proposalsCount and proposalsCount7d

fig, ax = plt.subplots(1, 2, figsize=(10, 5))
df["proposalsCount"].plot.hist(ax=ax[0], bins=500)
ax[0].set_title("proposalsCount")
df["proposalsCount7d"].plot.hist(ax=ax[1], bins=500)
ax[1].set_title("proposalsCount7d")
# log scale
ax[0].set_yscale("log")
ax[1].set_yscale("log")
# show plot
plt.show()
