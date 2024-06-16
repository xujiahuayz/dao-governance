import gzip
import json

from governenv.constants import SNAPSHOT_PATH_STATEMENTS, SNAPSHOT_ENDPOINT
from governenv.graphql import graphdata, query_structurer

# get id from df_spaces for the first 500 spaces

BATCH_SIZE = 1_000
# check documentation: https://docs.snapshot.org/tools/api

series = "statements"
specs = """
    id
    ipfs
    about
    statement
    space
    delegate
    updated
    created
"""

last_created = 0
with gzip.open(SNAPSHOT_PATH_STATEMENTS, "wt") as f:
    while True:
        reservepara_query = query_structurer(
            series,
            specs,
            arg=f'first: {BATCH_SIZE}, skip: 1, orderBy: "created", orderDirection: asc, where: {{created_gte: {last_created}}}',
        )
        res = graphdata(reservepara_query, url=SNAPSHOT_ENDPOINT)
        if "data" in set(res) and res["data"][series]:
            rows = res["data"][series]
            f.write("\n".join([json.dumps(row) for row in rows]) + "\n")
            last_created = rows[-1]["created"]
        else:
            break
