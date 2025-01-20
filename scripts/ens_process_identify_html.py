"""
Script to identify whether the html files meet the criteria: 
Check whether the discussion thread have at least one discussion
"""

import gzip
import json
import math
import time
import glob

import tiktoken
from tqdm import tqdm

from governenv.constants import DATA_DIR
from governenv.llm import ChatGPT
from governenv.prompts import IDF_INSTRUCT, IDF_PROMPT

tokenizer = tiktoken.encoding_for_model("gpt-4o")


llm = ChatGPT()

if __name__ == "__main__":

    # check fetched idf
    fetched_idf = [
        _.split("/")[-1].split(".")[0]
        for _ in glob.glob(str(DATA_DIR / "ens_idf" / "*.json"))
    ]

    with gzip.open(DATA_DIR / "ens_html.jsonl.gz", "rt") as gz_f:
        for line in tqdm(gz_f):
            data = json.loads(line.strip())
            id = data["id"]
            url = data["url"]
            html = data["html"]

            if id in fetched_idf:
                continue

            time.sleep(1)

            try:
                # identify if the html meets the criteria
                idf_res = llm(
                    instruction=IDF_INSTRUCT,
                    message=IDF_PROMPT.format(content=html),
                    logprobs=True,
                    top_logprobs=2,
                )

                idf, prob = idf_res if isinstance(idf_res, tuple) else (idf_res, None)

                first_prob = prob[0]
                yes_prob = (
                    math.exp(first_prob.logprob)
                    if "Yes" in first_prob.token
                    else 1 - math.exp(first_prob.logprob)
                )

                idf_dict = {
                    "url": url,
                    "idf": idf,
                    "yes_prob": yes_prob,
                }

                with open(
                    DATA_DIR / "ens_idf" / f"{id}.json", "w", encoding="utf-8"
                ) as f:
                    json.dump(idf_dict, f)

            except Exception as e:  # pylint: disable=broad-except
                time.sleep(2)
                print(f"Error processing {url}: {e}")

    res_dict = {}

    with gzip.open(DATA_DIR / "ens_html.jsonl.gz", "rt") as gz_f:
        for line in tqdm(gz_f):
            data = json.loads(line.strip())
            id = data["id"]
            url = data["url"]
            html = data["html"]

            if id in fetched_idf:
                with open(
                    DATA_DIR / "ens_idf" / f"{id}.json", "r", encoding="utf-8"
                ) as f:
                    idf_dict = json.load(f)

                res_dict[url] = {
                    "idf": idf_dict["idf"],
                    "yes_prob": idf_dict["yes_prob"],
                    "html": html,
                }

    with open(DATA_DIR / "ens_idf.json", "w", encoding="utf-8") as f:
        json.dump(res_dict, f)
