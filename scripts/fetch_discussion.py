"""Script to process discussion data for regression analysis."""

import glob
import time
import os

import pandas as pd
import requests
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
)
from tqdm import tqdm

from governenv.constants import HEADERS, DATA_DIR
from governenv.utils import kw_filt
from scripts.process_event_study import df_proposals_adj


@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=4, max=10),
    retry=retry_if_exception_type(Exception),
)
def fetch_http_response(url: str, timeout: int = 10) -> str:
    """
    Fetches the HTTP response from a given URL.
    """
    time.sleep(1)  # to avoid rate limiting
    response = requests.get(url, headers=HEADERS, timeout=timeout)

    # if the status_code is not 200, raise an error
    if response.status_code != 200:
        raise Exception(f"{response.status_code}")

    return response.text


if __name__ == "__main__":

    # Load the proposal data with discussion info
    df_proposals_adj = df_proposals_adj.loc[
        df_proposals_adj["have_discussion"] == True, ["id", "discussion"]
    ]

    # Apply keyword filtering on discussion URLs
    df_proposals_adj["discussion_kw_filtered"] = df_proposals_adj["discussion"].apply(
        kw_filt
    )
    df_proposals_discuss = df_proposals_adj.loc[
        df_proposals_adj["discussion_kw_filtered"] == True
    ]

    os.makedirs(DATA_DIR / "discussion", exist_ok=True)
    finished_files = glob.glob(str(DATA_DIR / "discussion" / "*.html"))
    finished_ids = [file.split("/")[-1].replace(".html", "") for file in finished_files]

    print(len(finished_ids))

    # random shuffle the dataframe rows
    df_proposals_discuss = df_proposals_discuss.sample(
        frac=1, random_state=42
    ).reset_index(drop=True)

    # Fetch and save the discussion content for each proposal
    access_deny = {
        "id": [],
        "url": [],
    }

    for _, row in tqdm(
        df_proposals_discuss.iterrows(), total=len(df_proposals_discuss)
    ):
        proposal_id = row["id"]
        discussion_url = row["discussion"]
        if str(proposal_id) in finished_ids:
            continue
        try:
            content = fetch_http_response(discussion_url)
            # check if content is empty
            if not content:
                raise Exception(f"Empty content from {discussion_url}")

            with open(
                DATA_DIR / "discussion" / f"{proposal_id}.html",
                "w",
                encoding="utf-8",
            ) as f:
                f.write(content)
        except Exception as e:
            print(f"Failed to fetch discussion for url {discussion_url}: {e}")
            if "403" in str(e):
                access_deny["id"].append(proposal_id)
                access_deny["url"].append(discussion_url)

    access_deny_df = pd.DataFrame(access_deny)
