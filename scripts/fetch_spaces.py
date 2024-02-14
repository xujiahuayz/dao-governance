import gzip
import json

from governenv.constants import SNAPSHOT_PATH
from governenv.graphql import graphdata, query_structurer

BATCH_SIZE = 1_000
# check documentation: https://docs.snapshot.org/tools/api
SNAPSHOT_ENDPOINT = "https://hub.snapshot.org/graphql"

series = "spaces"
specs = """
    id
    name
    private
    about
    avatar
    terms
    location
    website
    twitter
    github
    coingecko
    email
    network
    symbol
    skin
    domain
    strategies {
      name
      network
      params
    }
    admins
    members
    moderators
    filters {
      minScore
      onlyMembers
    }
    plugins
    voting {
      delay
      period
      type
      quorum
      blind
      hideAbstain
      privacy
      aliased
    }
    categories
    validation {
      name
      params
    }
    voteValidation {
      name
      params
    }
    delegationPortal {
      delegationType
      delegationContract
      delegationApi
    }
    treasuries {
      name
      address
      network
    }
    activeProposals
    proposalsCount
    proposalsCount7d
    votesCount
    votesCount7d
    parent {
      id
    }
    children {
      id
    }
    guidelines
    template
    verified
    flagged
    hibernated
    turbo
    rank
    created
"""

last_created = 0
with gzip.open(SNAPSHOT_PATH, "wt") as f:
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
