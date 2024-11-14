"""
Fetch the http response of the discussion links
"""

import pickle
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
    # unpickle data_unique
    with open(DATA_DIR / "discussion_links.pkl", "rb") as f:
        data_unique = pickle.load(f)
        print(f"Data length before filtering: {len(data_unique)}")

    # filter discussions
    data_unique = slash_filt(kw_filt(data_unique))
    print(f"Data length after filtering: {len(data_unique)}")

    fetched_data = [
        _.split("/")[-1].split(".")[0] for _ in glob(str(DATA_DIR / "html" / "*.html"))
    ]

    # fetch http response
    for i, (k, v) in tqdm(enumerate(data_unique.items()), total=len(data_unique)):
        if str(i) in fetched_data:
            continue
        try:
            # save the html
            html = fetch_http_response(v)
            with open(DATA_DIR / "html_200" / f"{i}.html", "w", encoding="utf-8") as f:
                f.write(html)
        except Exception as e:
            print(f"Error fetching {v}: {e}")

        time.sleep(2)
