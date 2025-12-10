"""Script to merge the Whale and Small voter participation data"""

import pandas as pd

from governenv.constants import PROCESSED_DATA_DIR

df_voter = pd.read_csv(PROCESSED_DATA_DIR / "proposals_voter.csv")
df_user = pd.read_csv(PROCESSED_DATA_DIR / "proposal_user.csv")

df_merged = df_voter.merge(df_user, on=["id"], how="left")
df_merged.to_csv(PROCESSED_DATA_DIR / "proposals_voter_user.csv", index=False)
