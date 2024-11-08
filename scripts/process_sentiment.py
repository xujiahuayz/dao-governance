import gzip
import json
import math
import pickle

import requests

from governenv.constants import DATA_DIR, HEADERS
from governenv.llm import ChatGPT
from governenv.prompts import EVAL_INSTRUCT, EVAL_PROMPT, IDF_INSTRUCT, IDF_PROMPT


if __name__ == "__main__":

    llm = ChatGPT()

    # unpickle data_unique
    with open(DATA_DIR / "discussion_links.pkl", "rb") as f:
        data_unique = pickle.load(f)
        print(f"Data length before filtering: {len(data_unique)}")

    # filter discussions
    data_unique = slash_filt(kw_filt(data_unique))
    print(f"Data length after filtering: {len(data_unique)}")

    for idx, (_, url) in enumerate(data_unique.items()):

        try:
            http_response = requests.get(url, headers=HEADERS, timeout=10).text

            idf = llm(
                instruction=IDF_INSTRUCT,
                message=IDF_PROMPT.format(http_response=http_response),
            )
            print("\n")
            print(f"URL: {url}")
            if idf == "Yes":
                eval_res = llm(
                    instruction=EVAL_INSTRUCT,
                    message=EVAL_PROMPT.format(http_response=http_response),
                    logprobs=True,
                    top_logprobs=2,
                )

                eval, prob = (
                    eval_res if isinstance(eval_res, tuple) else (eval_res, None)
                )
                eval_prob = [_ for _ in prob if _.token in [" Yes", " No"]]
                yes_prob = [
                    math.exp(binary.logprob)
                    for top_log_probs in eval_prob
                    for binary in top_log_probs.top_logprobs
                    if binary.token == " Yes"
                ]

                class_prob = {
                    "Support": yes_prob[0],
                    "Professionalism": yes_prob[1],
                    "Objectiveness": yes_prob[2],
                }

                print(f"Evaluation: {eval}")
                print(f"Class Probabilities: {class_prob}")

            else:
                print("IDF: Not a forum discussion")

            if idx == 5:
                break
        except Exception as e:  # pylint: disable=broad-except
            print(f"URL: {url} failed with error: {e}")
