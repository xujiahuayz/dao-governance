import gzip
import json

from governenv.constants import SNAPSHOT_PATH_VOTES, SNAPSHOT_ENDPOINT
from governenv.graphql import graphdata, query_structurer
from scripts.process_spaces import df_spaces

# get id from df_spaces for the first 500 spaces

spaces = df_spaces[df_spaces["proposalsCount"] >= 1]["id"].values[:500]

BATCH_SIZE = 1_000
# check documentation: https://docs.snapshot.org/tools/api

series = "votes"
specs = """
    id
    ipfs
    voter
    created
    proposal {id}
    choice
    metadata
    reason
    app
    vp
    vp_by_strategy
    vp_state
"""

last_created = 0
res = {}
with gzip.open(SNAPSHOT_PATH_VOTES, "wt") as f:
    for space in spaces:
        print(space)
        while True:
            reservepara_query = query_structurer(
                series,
                specs,
                arg=f'first: {BATCH_SIZE}, where: {{created_gte: {last_created}, space: "{space}"}}'
                + ', skip: 1, orderBy: "created", orderDirection: asc',
            )
            res = graphdata(reservepara_query, url=SNAPSHOT_ENDPOINT)
            # if unauthoraized / forbidden, print res and break both while and for loops
            if "data" in res and res["data"][series]:
                rows = res["data"][series]
                f.write("\n".join([json.dumps(row) for row in rows]) + "\n")
                last_created = rows[-1]["created"]
            else:
                print(res)
                break
        if "error" in res:
            break
