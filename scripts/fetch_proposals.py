import gzip
import json

from governenv.constants import SNAPSHOT_PATH_PROPOSALS
from governenv.graphql import graphdata, query_structurer

BATCH_SIZE = 1_000
# check documentation: https://docs.snapshot.org/tools/api
SNAPSHOT_ENDPOINT = "https://hub.snapshot.org/graphql"

series = "proposals"
specs = """
    id
    ipfs
    author
    created
    updated
    space {id}
    network
    symbol
    type
    strategies {name}
    validation {name}
    plugins
    title
    body
    discussion
    choices
    start
    end
    quorum
    privacy
    snapshot
    state
    link
    app
    scores
    scores_by_strategy
    scores_state
    scores_updated
    votes
    flagged
"""

last_created = 0
with gzip.open(SNAPSHOT_PATH_PROPOSALS, "wt") as f:
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
