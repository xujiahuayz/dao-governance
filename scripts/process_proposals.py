import gzip
import json


from governenv.constants import SNAPSHOT_PATH_PROPOSALS

# load the data


with gzip.open(SNAPSHOT_PATH_PROPOSALS, "rt") as f:
    # load data and skip duplicates
    data = [json.loads(line) for line in f]

# remove duplicates

data_unique = [
    json.loads(line) for line in set([json.dumps(row, sort_keys=True) for row in data])
]
