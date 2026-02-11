"""
Script to fetch the risk-free rate from the Fama French library
"""

import ssl
import pandas as pd
from governenv.constants import DATA_DIR

FAMA_FRENCH_THREE_FACTORS_DAILY = (
    "https://mba.tuck.dartmouth.edu/pages/faculty/"
    + "ken.french/ftp/F-F_Research_Data_Factors_daily_CSV.zip"
)


# Create an SSL context that ignores SSL certificate verification
ssl._create_default_https_context = ssl._create_unverified_context


# read the data and ignore the first and last three rows
df_rf = pd.read_csv(
    FAMA_FRENCH_THREE_FACTORS_DAILY,
    skiprows=3,
    skipfooter=3,
    engine="python",
)

# rename the columns
df_rf.columns = ["Date", "Mkt-RF", "SMB", "HML", "RF"]
df_rf = df_rf[["Date", "RF"]]
df_rf["Date"] = pd.to_datetime(df_rf["Date"], format="%Y%m%d")

# Fill missing dates
date_range = pd.date_range(df_rf["Date"].min(), df_rf["Date"].max())
df_date_range = pd.DataFrame({"Date": date_range})
df_rf = pd.merge(df_date_range, df_rf, on="Date", how="left")
df_rf["Date"] = pd.to_datetime(df_rf["Date"]).dt.strftime("%Y-%m-%d")
df_rf["RF"].fillna(method="ffill", inplace=True)
df_rf["RF"] = df_rf["RF"] / 100  # convert to decimal
df_rf.rename(columns={"Date": "date", "RF": "rf"}, inplace=True)

# save the DataFrame
df_rf.to_csv(DATA_DIR / "rf.csv", index=False)
