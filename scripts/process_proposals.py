import pickle
from governenv.constants import SNAPSHOT_PATH_PROPOSALS, DATA_DIR
import gzip
import json


# load the data
with gzip.open(SNAPSHOT_PATH_PROPOSALS, "rt") as f:
    # load data and skip duplicates
    data = [json.loads(line) for line in f]

# remove duplicates and filter out proposals with not discussion link
data_unique = {
    w["id"]: w["discussion"]
    for line in set([json.dumps(row, sort_keys=True) for row in data])
    if len((w := json.loads(line))["discussion"]) > 5
}

# pickle data_unique
with open(DATA_DIR / "discussion_links.pkl", "wb") as f:
    pickle.dump(data_unique, f)
