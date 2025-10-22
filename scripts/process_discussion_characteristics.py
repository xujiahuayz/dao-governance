"""Script to process discussion data for regression analysis."""

import glob
import json

import pandas as pd
from governenv.constants import PROCESSED_DATA_DIR


sentiment_files = glob.glob("processed_data/sentiment/*.json")
sentiment_data = []

for file in sentiment_files:
    fid = file.split("/")[-1].replace(".json", "")
    with open(file, "r", encoding="utf-8") as f:
        data = json.load(f)
        data["id"] = fid
        sentiment_data.append(data)

df_sentiment = pd.DataFrame(sentiment_data)

# classfify the all scores into high and low based on 0
for col in ["Support", "Professionalism", "Objectiveness", "Unanimity"]:
    df_sentiment[col] = df_sentiment[col].apply(lambda x: 0 if x == 0 else 1)

df_sentiment.to_csv(
    PROCESSED_DATA_DIR / "proposals_adjusted_discussions.csv",
    index=False,
)
