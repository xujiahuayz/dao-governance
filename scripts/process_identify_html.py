"""
Script to identify whether the html files meet the criteria
"""

import gzip
import json
import math


import tiktoken
from tqdm import tqdm

from governenv.constants import DATA_DIR
from governenv.llm import ChatGPT
from governenv.prompts import IDF_INSTRUCT, IDF_PROMPT

tokenizer = tiktoken.encoding_for_model("gpt-4o")


idf_dict = {}

llm = ChatGPT()

if __name__ == "__main__":

    with gzip.open(DATA_DIR / "html.jsonl.gz", "rt") as gz_f:
        for idx, line in tqdm(enumerate(gz_f)):
            data = json.loads(line.strip())
            url = data["url"]
            html = data["html"]

            try:
                # identify if the html meets the criteria
                idf_res = llm(
                    instruction=IDF_INSTRUCT,
                    message=IDF_PROMPT.format(http_response=html),
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

                idf_dict[url] = {
                    "idf": idf,
                    "yes_prob": yes_prob,
                }
            except Exception as e:
                print(f"Error processing {url}: {e}")

    with open(DATA_DIR / "idf.json", "w", encoding="utf-8") as f:
        json.dump(idf_dict, f, indent=2)
