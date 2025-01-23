"""
Fetch the http response of the discussion links
"""

import json
import time
from glob import glob

import requests
from tqdm import tqdm

from governenv.constants import DATA_DIR, HEADERS
from governenv.utils import kw_filt, slash_filt


def fetch_http_response(url: str, timeout: int = 10) -> str:
    """
    Fetches the HTTP response from a given URL.
    """
    response = requests.get(url, headers=HEADERS, timeout=timeout)

    # if the status_code is not 200, raise an error
    if response.status_code != 200:
        raise Exception(f"Status code: {response.status_code}")

    return response.text


if __name__ == "__main__":

    HTML_200_DIR = DATA_DIR / "html_200"

    # unpickle data_unique
    with open(DATA_DIR / "ens_snapshot_filtered.json", "rb") as f:
        data_unique = json.load(f)
        print(f"Data length before filtering: {len(data_unique)}")

    # filter discussions
    data_unique = slash_filt(kw_filt(data_unique))
    print(f"Data length after filtering: {len(data_unique)}")

    fetched_data = [
        _.split("/")[-1].split(".")[0] for _ in glob(str(HTML_200_DIR / "*.html"))
    ]

    # fetch http response
    for id, url in tqdm(data_unique.items(), total=len(data_unique)):
        if id in fetched_data:
            continue
        try:
            # save the html
            html = fetch_http_response(url)
            with open(HTML_200_DIR / f"{id}.html", "w", encoding="utf-8") as f:
                f.write(html)
        except Exception as e:
            print(f"Error fetching {url}: {e}")

        time.sleep(2)
