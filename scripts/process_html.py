"""
Script to aggregate all the html files in the data folder into a single jsonl file
"""

import gzip
import json
import pickle
from glob import glob

from bs4 import BeautifulSoup
from tqdm import tqdm

from governenv.constants import DATA_DIR
from governenv.utils import kw_filt, slash_filt


def distill_html(html: str) -> str:
    """
    Function to distill the html
    """
    # Parse the HTML
    soup = BeautifulSoup(html, "html.parser")

    # Remove irrelevant tags (scripts, styles, footers, navs, etc.)
    for tag in soup(
        ["script", "style", "header", "footer", "nav", "aside", "form", "link", "meta"]
    ):
        tag.decompose()

    # Extract text content from discussion-relevant tags
    relevant_content = soup.find_all(["div", "p", "li", "article", "section"])

    # Combine and clean the text
    cleaned_text = "\n\n".join(
        tag.get_text(strip=True) for tag in relevant_content if tag.get_text(strip=True)
    )

    return cleaned_text


if __name__ == "__main__":

    # unpickle data_unique
    with open(DATA_DIR / "discussion_links.pkl", "rb") as f:
        data_unique = pickle.load(f)
        print(f"Data length before filtering: {len(data_unique)}")

    # filter discussions
    data_unique = slash_filt(kw_filt(data_unique))
    print(f"Data length after filtering: {len(data_unique)}")

    fetched_data = [
        _.split("/")[-1].split(".")[0]
        for _ in glob(str(DATA_DIR / "html_200" / "*.html"))
    ]

    # save the html
    with gzip.open(DATA_DIR / "html.jsonl.gz", "wt") as gz_f:
        for i, (k, v) in tqdm(enumerate(data_unique.items())):
            if str(i) in fetched_data:
                # save the html
                with open(
                    DATA_DIR / "html_200" / f"{i}.html", "r", encoding="utf-8"
                ) as f:
                    html = f.read()

                # distill the html
                html_distilled = distill_html(html)

                json.dump({"url": v, "html": html_distilled}, gz_f)
                gz_f.write("\n")
