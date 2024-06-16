import gzip
import json

from governenv.constants import SNAPSHOT_PATH_DELEGATE
from governenv.graphql import graphdata, query_structurer
from scripts.process_spaces import df_spaces

# get id from df_spaces for the first 500 spaces
GRAPH_SNAPSHOT_ENDPOINT = (
    "https://api.thegraph.com/subgraphs/name/snapshot-labs/snapshot"
)

spaces = df_spaces[df_spaces["proposalsCount"] >= 1]["id"].values[:500]

BATCH_SIZE = 1_000

series = "delegations"
specs = """
    id
    delegator
    space
    delegate
    timestamp
"""

last_ts = 0
with gzip.open(SNAPSHOT_PATH_DELEGATE, "wt") as f:
    while True:
        reservepara_query = query_structurer(
            series,
            specs,
            arg=f"first: {BATCH_SIZE}, orderBy: timestamp, orderDirection: asc, where: {{ timestamp_gt: {last_ts} }}",
        )
        res = graphdata(reservepara_query, url=GRAPH_SNAPSHOT_ENDPOINT)
        if "data" in set(res) and res["data"][series]:
            rows = res["data"][series]
            f.write("\n".join([json.dumps(row) for row in rows]) + "\n")
            last_ts = rows[-1]["timestamp"]
            print(last_ts)
        else:
            break
