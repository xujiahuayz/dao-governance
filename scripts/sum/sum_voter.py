"""Script to merge the Whale and Small voter participation data"""

import numpy as np
import pandas as pd

from governenv.constants import PROCESSED_DATA_DIR

USER_CHAR = ["voter_user", "whale_user", "non_whale_user"]

df_voter = pd.read_csv(PROCESSED_DATA_DIR / "proposals_voter.csv")
df_user = pd.read_csv(PROCESSED_DATA_DIR / "proposal_user.csv")

# Remove users in spaces without infrastructure
df_user["infrastructure"] = (
    df_user.groupby("space")["voter_user"].transform("sum").gt(0).astype(int)
)
df_user.loc[df_user["infrastructure"] == 0, USER_CHAR] = np.nan
USER_CHAR.append("infrastructure")
df_user = df_user.drop(columns=["space"])

df_merged = df_voter.merge(df_user, on=["id"], how="left")
df_merged.to_csv(PROCESSED_DATA_DIR / "proposals_voter_user.csv", index=False)
