"""Script to implement Loughran-McDonald NLP on proposal discussions."""

import re
import pandas as pd

from governenv.constants import DATA_DIR
from scripts.process.merge_discussion import df_proposals


# Load the Loughran-McDonald dictionary
lm = pd.read_csv(
    DATA_DIR / "lexicons" / "Loughran-McDonald_MasterDictionary_1993-2024.csv"
)

# Create sets for each sentiment category
pos = set(lm.loc[lm["Positive"] > 0, "Word"].astype(str).str.lower())
neg = set(lm.loc[lm["Negative"] > 0, "Word"].astype(str).str.lower())
cpx = set(lm.loc[lm["Complexity"] > 0, "Word"].astype(str).str.lower())


def sentiment_score(text, pos_set, neg_set) -> float:
    """
    Function to compute sentiment score based on Loughran-McDonald dictionary.
    """
    words = re.findall(r"[A-Za-z]+", text.lower())
    pos_n = sum(w in pos_set for w in words)
    neg_n = sum(w in neg_set for w in words)

    denom = pos_n + neg_n
    if denom == 0:
        return 0.0  # neutral if no LM words
    return (pos_n - neg_n) / denom


def complexity_score(text, cpx_set) -> float:
    """
    Function to compute complexity score as per Loughran-McDonald dictionary.
    """
    words = re.findall(r"[A-Za-z]+", text.lower())
    n_words = len(words)
    n_sent = max(1, len(re.split(r"[.!?]+", text)))

    cpx_n = sum(w in cpx_set for w in words)

    return 0.4 * (n_words / n_sent + 100 * cpx_n / max(1, n_words))


def informativeness_score(text) -> float:
    """
    Function to compute informativeness score as ratio of numbers to words.
    """
    words = len(text.split())
    numbers = len(re.findall(r"\d+(\.\d+)?", text))
    return numbers / max(1, words)


df_proposals["post_sentiment"] = df_proposals["post"].apply(
    lambda x: sentiment_score(x, pos, neg)
)
df_proposals["post_complexity"] = df_proposals["post"].apply(
    lambda x: complexity_score(x, cpx)
)
df_proposals["post_informativeness"] = df_proposals["post"].map(informativeness_score)
