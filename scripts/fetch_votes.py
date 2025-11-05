"""Script to fetch votes given a id"""

import glob

import pandas as pd
from tqdm import tqdm

from governenv.constants import DATA_DIR, PROCESSED_DATA_DIR, SNAPSHOT_ENDPOINT
from governenv.graphql import query_id
from governenv.queries import VOTES


# Load proposals
df_proposals_adj = pd.read_csv(PROCESSED_DATA_DIR / "proposals_with_sc.csv")
proposals_list = df_proposals_adj["id"].tolist()

# Check existing files to avoid re-fetching
save_path = DATA_DIR / "snapshot" / "votes"
files_list = glob.glob(str(save_path / "*.jsonl"))
files_list_str = [file.split("/")[-1].split(".")[0] for file in files_list]
todos = [idx for idx in proposals_list if str(idx) not in files_list_str]

for idx in tqdm(todos):
    if idx in files_list_str:
        continue
    else:
        try:
            query_id(
                save_path=save_path,
                idx=idx,
                idx_var="proposal",
                time_var="created",
                series="votes",
                query_template=VOTES,
                end_point=SNAPSHOT_ENDPOINT,
                batch_size=1000,
            )
        except Exception as e:
            print(f"Error fetching votes for proposal {idx}: {e}")
            continue
