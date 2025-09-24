"""Fetch and store proposals data from Snapshot API."""

from governenv.constants import SNAPSHOT_PATH_PROPOSALS
from governenv.queries import PROPOSALS
from governenv.graphql import query


query(
    save_path=SNAPSHOT_PATH_PROPOSALS,
    series="proposals",
    query_template=PROPOSALS,
    batch_size=1000,
)
