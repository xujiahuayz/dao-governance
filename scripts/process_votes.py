import gzip
import json
import pandas as pd

from governenv.constants import SNAPSHOT_PATH_VOTES, SNAPSHOT_PATH_PROPOSALS

# load the data


with gzip.open(SNAPSHOT_PATH_VOTES, "rt") as f:
    data = [json.loads(line) for line in f]


data_unique = [
    json.loads(line) for line in set([json.dumps(row, sort_keys=True) for row in data])
]

df_voter = pd.DataFrame(
    {
        "voter": item["voter"],
        "voting_power": item["vp"],
        "proposal": item["proposal"]["id"],
    }
    for item in data_unique
)


with gzip.open(SNAPSHOT_PATH_PROPOSALS, "rt") as f:
    # load data and skip duplicates
    data_proposal = [json.loads(line) for line in f]

# remove duplicates

data_unique_proposal = [
    json.loads(line)
    for line in set([json.dumps(row, sort_keys=True) for row in data_proposal])
]

df_proposal = pd.DataFrame(
    {
        "proposal": item["id"],
        "space": item["space"]["id"],
    }
    for item in data_unique_proposal
)

# merge voter and proposal dataframes by proposal
df = pd.merge(df_voter, df_proposal, on="proposal")

# select the top 2 voters for each space based on voting power
df_topvoters = df.groupby(["space", "voter"]).agg({"voting_power": "sum"}).reset_index()
df_topvoters = (
    df_topvoters.sort_values(by="voting_power", ascending=False)
    .groupby("space")
    .head(2)
)
