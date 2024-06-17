import gzip
import json

import matplotlib.pyplot as plt
import pandas as pd

from governenv.constants import SNAPSHOT_PATH_DELEGATE

# load the data


with gzip.open(SNAPSHOT_PATH_DELEGATE, "rt") as f:
    # load data and skip duplicates
    data = [json.loads(line) for line in f]

df = pd.DataFrame(data)

# take unique by delegator, delegate, space
df_unique = df.drop_duplicates(subset=["delegator", "delegate", "space"])

# check df and df_unique row number
df.shape == df_unique.shape

# bar plot of the number of delegations per space - for the top 10 spaces
df_unique["space"].value_counts().head(20).plot(kind="bar")

# bar plot of the number of delegates per space - for the top 10 spaces
df_unique.drop_duplicates(subset=["delegate", "space"])["space"].value_counts().head(
    20
).plot(kind="bar")
