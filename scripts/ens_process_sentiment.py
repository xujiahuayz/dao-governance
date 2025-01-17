import math
import json


from governenv.constants import DATA_DIR
from governenv.llm import ChatGPT
from governenv.prompts import EVAL_INSTRUCT, EVAL_PROMPT

if __name__ == "__main__":

    senti_res = {}

    llm = ChatGPT()

    with open(DATA_DIR / "ens_idf.json", "r", encoding="utf-8") as f:
        idf = json.load(f)

    for idx, (url, info) in enumerate(idf.items()):

        if info["idf"] == "No":
            continue
        try:
            eval_res = llm(
                instruction=EVAL_INSTRUCT,
                message=EVAL_PROMPT.format(content=info["html"]),
                logprobs=True,
                top_logprobs=2,
            )

            eval, prob = eval_res if isinstance(eval_res, tuple) else (eval_res, None)
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
                "Unanimity": yes_prob[3],
            }

            print(f"URL: {url}")
            print(f"Evaluation: {eval}")
            print(f"Class Probabilities: {class_prob}")

            senti_res[url] = {
                "evaluation": eval,
                "class_prob": class_prob,
            }

        except Exception as e:  # pylint: disable=broad-except
            print(f"URL: {url} failed with error: {e}")

    with open(DATA_DIR / "ens_senti.json", "w", encoding="utf-8") as f:
        json.dump(senti_res, f, indent=4)
