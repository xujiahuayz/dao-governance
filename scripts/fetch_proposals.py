"""Fetch and store spaces data from Snapshot API."""

from governenv.constants import (
    SNAPSHOT_PATH,
    SNAPSHOT_PATH_PROPOSALS,
    SNAPSHOT_PATH_STATEMENTS,
    SNAPSHOT_PATH_DELEGATE,
    GRAPH_SNAPSHOT_ENDPOINT,
    SNAPSHOT_ENDPOINT,
    SNAPSHOT_PATH_NETWORKS,
)
from governenv.settings import THEGRAPH_API_KEY
from governenv.queries import SPACES, PROPOSALS, STATEMENTS, DELEGATIONS, NETWORKS
from governenv.graphql import query, query_single


# # Fetch spaces data from Snapshot API
# query(
#     save_path=SNAPSHOT_PATH,
#     series="spaces",
#     query_template=SPACES,
#     end_point=SNAPSHOT_ENDPOINT,
#     time_var="created",
#     batch_size=1000,
# )

# Fetch proposals data from Snapshot API
query(
    save_path=SNAPSHOT_PATH_PROPOSALS,
    series="proposals",
    query_template=PROPOSALS,
    end_point=SNAPSHOT_ENDPOINT,
    time_var="created",
    batch_size=1000,
)

# # Fetch statements data from Snapshot API
# query(
#     save_path=SNAPSHOT_PATH_STATEMENTS,
#     series="statements",
#     query_template=STATEMENTS,
#     end_point=SNAPSHOT_ENDPOINT,
#     time_var="created",
#     batch_size=1000,
# )

# # Fetch delegation data from Snapshot API
# query(
#     save_path=SNAPSHOT_PATH_DELEGATE,
#     series="delegations",
#     query_template=DELEGATIONS,
#     end_point=GRAPH_SNAPSHOT_ENDPOINT,
#     time_var="timestamp",
#     batch_size=1000,
#     headers={"Authorization": f"Bearer {THEGRAPH_API_KEY}"},
# )

# # Fetch networks data from Snapshot API
# query_single(
#     save_path=SNAPSHOT_PATH_NETWORKS,
#     series="networks",
#     query_template=NETWORKS,
#     end_point=SNAPSHOT_ENDPOINT,
# )

# import json
# import gzip
# from governenv.graphql import query_structurer, graphdata

# series = "networks"
# end_point = SNAPSHOT_ENDPOINT
# query_template = NETWORKS

# with gzip.open(SNAPSHOT_PATH_NETWORKS, "at") as f:
#     # Query data
#     reservepara_query = query_structurer(
#         series,
#         query_template,
#     )
#     res = graphdata(reservepara_query, url=end_point)
#     print(res)
#     if "data" in set(res):
#         if res["data"][series]:
#             # Process fetched rows
#             rows = res["data"][series]
#             # Write rows to file and break the loop
#             f.write("\n".join([json.dumps(row) for row in rows]) + "\n")
#     else:
#         raise ValueError("Error in fetching data")
