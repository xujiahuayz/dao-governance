"""Script to fetch votes given a id"""

import glob
from tqdm import tqdm

from governenv.constants import DATA_DIR, SNAPSHOT_ENDPOINT
from governenv.graphql import query_id
from governenv.queries import VOTES

from scripts.process_event_study import df_proposals_adj


# Fetch votes
save_path = DATA_DIR / "snapshot" / "votes"
files_list = glob.glob(str(save_path / "*.jsonl"))
files_list_str = [file.split("/")[-1].split(".")[0] for file in files_list]

for idx in tqdm(df_proposals_adj["id"].tolist(), total=len(df_proposals_adj)):
    if idx in files_list_str:
        continue
    else:
        print(f"Fetching votes for proposal {idx}")
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
