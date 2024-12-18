"""
For each discussion forum URLs, extract authors and their associated discussions
"""


import requests
import json
from bs4 import BeautifulSoup
from governenv.constants import DATA_DIR
from governenv.settings import HEADERS 


with open(DATA_DIR / "ens_snapshot_filtered.json", "r") as f:
    data = json.load(f)

all_discussions = []

for id, url in data.items():
    response = requests.get(url, headers=HEADERS) # The function can still run without the headers parameter in .env 

    if response.status_code == 200:

        html_content = response.text

        soup = BeautifulSoup(html_content, "html.parser")

        posts = soup.find_all("div", {"class": "topic-body crawler-post"})

        discussion = []

        for post in posts:
            # Extract author name
            author_tag = post.find("span", {"itemprop": "name"})
            author_name = author_tag.get_text(strip=True)

            # Extract text inside <div class='post' itemprop='text'>
            content_div = post.find("div", {"class": "post", "itemprop": "text"})
            if content_div:
                # Remove all <blockquote> tags
                for blockquote in content_div.find_all("blockquote"):
                    blockquote.decompose() 

                content = content_div.get_text(" ", strip=True)

                discussion.append({"author": author_name, "content": content})

        all_discussions.append(
            {"id": id, "discussion_url": url, "discussion": discussion}
        )
    else:
        print(f"Failed to fetch URL: {url} (Status code: {response.status_code})")

with open(DATA_DIR / "ens_authors.json", "w") as file:
    json.dump(all_discussions, file, indent=4)
