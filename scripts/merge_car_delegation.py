"""Script to process delegation data."""

import gzip
import json

import pandas as pd

from governenv.constants import DATA_DIR, PROCESSED_DATA_DIR


snapshot_delegate = []
with gzip.open(DATA_DIR / "snapshot_delegate.jsonl.gz", "rt", encoding="utf-8") as f:
    for line in f:
        snapshot_delegate.append(json.loads(line))

panel_start = pd.read_csv(PROCESSED_DATA_DIR / "event_study_panel_created.csv")

[_ for _ in snapshot_delegate if _[""]]
