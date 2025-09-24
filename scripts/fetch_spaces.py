"""Fetch and store spaces data from Snapshot API."""

from governenv.constants import SNAPSHOT_PATH
from governenv.queries import SPACES
from governenv.graphql import query


query(
    save_path=SNAPSHOT_PATH,
    series="spaces",
    query_template=SPACES,
    batch_size=1000,
)
