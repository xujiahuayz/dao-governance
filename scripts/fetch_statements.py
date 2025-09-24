"""Fetch and store statements data from Snapshot API."""

from governenv.constants import SNAPSHOT_PATH_STATEMENTS
from governenv.queries import STATEMENTS
from governenv.graphql import query


query(
    save_path=SNAPSHOT_PATH_STATEMENTS,
    series="statements",
    query_template=STATEMENTS,
    batch_size=1000,
)
