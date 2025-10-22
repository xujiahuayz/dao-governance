"""Script to implement LDA topic modeling on proposal texts"""

from pathlib import Path

import re
import string
import joblib
import numpy as np
import pandas as pd
from sklearn.decomposition import LatentDirichletAllocation
from sklearn.feature_extraction.text import CountVectorizer, ENGLISH_STOP_WORDS

from governenv.constants import PROCESSED_DATA_DIR
from scripts.process_event_study import df_proposals_adj

ID_COL = "id"
TEXT_COL = "body"
OUT_DIR = f"{PROCESSED_DATA_DIR}/lda_body"

N_TOPICS = 7
MAX_FEATURES = 30000
MIN_DF = 5  # int count or float proportion (e.g., 0.01)
MAX_DF = 0.7  # ignore very common tokens
NGRAM_MAX = 1  # keep at 1 to avoid bigram artifacts like "reward standard"
RANDOM_STATE = 42
MAX_ITER = 20
LEARNING_METHOD = "batch"  # "batch" or "online"

# Domain stopwords to reduce UI/ticker noise (extend as needed)
DOMAIN_STOPWORDS = {
    # UI / form junk
    "click",
    "select",
    "current",
    "standard",
    "daily",
    "limit",
    # odd short tokens seen earlier
    "st",
    "crts",
    "om",
    # proper nouns & tickers dominating topics (tune to taste)
    "avt",
    "aventus",
    "gnosis",
    "fwb",
    "lon",
    "usdc",
    "usdt",
    "dai",
    "weth",
    "eth",
    "base",
    "ethereum",
}
STOPWORDS = list(ENGLISH_STOP_WORDS.union(DOMAIN_STOPWORDS))
# ==========================================

URL_RE = re.compile(r"https?://\S+|www\.\S+")
CODE_RE = re.compile(r"`{1,3}.*?`{1,3}", re.DOTALL)
MULTISPACE_RE = re.compile(r"\s+")


def basic_clean(text: str) -> str:
    """Basic text cleaning: lower, strip URLs, code blocks, digits, extra spaces."""
    if not isinstance(text, str):
        return ""
    t = CODE_RE.sub(" ", text)
    t = URL_RE.sub(" ", t)
    t = t.lower()
    t = t.translate(str.maketrans("", "", string.digits))
    t = t.replace("’", "'")
    t = MULTISPACE_RE.sub(" ", t).strip()
    return t


def top_words_for_topic(components_row, feature_names, n_top=15):
    """Get top n words and their weights for a given topic component row."""
    idx = np.argsort(components_row)[::-1][:n_top]
    words = [feature_names[i] for i in idx]
    weights = [components_row[i] for i in idx]
    return words, weights


def row_entropy(p: np.ndarray) -> float:
    """Compute entropy of a probability distribution row."""
    p_safe = np.clip(p, 1e-12, 1.0)
    return float(-(p_safe * np.log(p_safe)).sum())


if __name__ == "__main__":
    out_dir = Path(OUT_DIR)
    out_dir.mkdir(parents=True, exist_ok=True)

    # ---- Load + restrict to one row per proposal (index == EVENT_WINDOW) ----
    df = df_proposals_adj.copy()

    # ---- Clean + drop empties ----
    df["_text_clean"] = df[TEXT_COL].apply(basic_clean)
    df = df[df["_text_clean"].str.len() > 0].copy()
    if df.empty:
        raise ValueError("No non-empty documents after cleaning.")

    # ---- Vectorize ----
    vectorizer = CountVectorizer(
        stop_words=STOPWORDS,
        max_features=MAX_FEATURES,
        min_df=MIN_DF,
        max_df=MAX_DF,
        ngram_range=(1, NGRAM_MAX),
        # only words with ≥3 chars; allow ' and - inside words
        token_pattern=r"(?u)\b[a-z][a-z'\-]{2,}\b",
    )
    X = vectorizer.fit_transform(df["_text_clean"])
    vocab = vectorizer.get_feature_names_out()

    # ---- Fit LDA ----
    lda = LatentDirichletAllocation(
        n_components=N_TOPICS,
        max_iter=MAX_ITER,
        random_state=RANDOM_STATE,
        learning_method=LEARNING_METHOD,
        n_jobs=-1,
        evaluate_every=0,
    ).fit(X)

    # ---- Save topics overview ----
    rows = []
    for k in range(N_TOPICS):
        words, weights = top_words_for_topic(lda.components_[k], vocab, n_top=20)
        rows.append(
            {
                "topic_id": k,
                "top_words": ", ".join(words[:15]),
                "top_terms_with_weights": "; ".join(
                    f"{w}:{round(float(wt), 4)}" for w, wt in zip(words, weights)
                ),
            }
        )
    topics_df = pd.DataFrame(rows).sort_values("topic_id")
    topics_df.to_csv(PROCESSED_DATA_DIR / "proposals_adjusted_topics.csv", index=False)

    # ---- Per-document topic mixtures + entropy ----
    doc_topic = lda.transform(X)  # rows sum ~1
    dominant_topic = doc_topic.argmax(axis=1)
    dominant_prob = doc_topic.max(axis=1)
    entropy = np.apply_along_axis(row_entropy, 1, doc_topic)

    doc_topics_df = pd.DataFrame(
        doc_topic, columns=[f"topic_{i}" for i in range(N_TOPICS)]
    )
    doc_topics_df.insert(0, "dominant_topic", dominant_topic.astype(int))
    doc_topics_df.insert(1, "dominant_prob", dominant_prob.astype(float))
    doc_topics_df.insert(2, "topic_entropy", entropy.astype(float))
    doc_topics_df.insert(0, ID_COL, df[ID_COL].values)

    # ---- Build 7 bucket shares from 7 topics (1:1 mapping) ----
    # Buckets (based on your 7-topic interpretation):
    #   00 Voting/Participation
    #   01 Incentives & NFTs
    #   02 Governance Council/Process
    #   03 Ecosystem & Integrations
    #   04 Grants/Programs
    #   05 Liquidity/DeFi Mechanics
    #   06 Treasury Ops & Budget

    bucket_map = {
        "bucket_vote_share": ["topic_0"],
        "bucket_incentives_share": ["topic_1"],
        "bucket_govcouncil_share": ["topic_2"],
        "bucket_ecosys_share": ["topic_3"],
        "bucket_grants_share": ["topic_4"],
        "bucket_liquidity_share": ["topic_5"],
        "bucket_treasuryops_share": ["topic_6"],
    }

    # Create bucket shares (sum over listed topics; safe if some topic_* cols missing)
    for bcol, topics in bucket_map.items():
        doc_topics_df[bcol] = sum(doc_topics_df.get(t, 0.0) for t in topics)

    bucket_cols = list(bucket_map.keys())

    # Dominant bucket index 0..6
    bucket_argmax = np.asarray(doc_topics_df[bucket_cols].values).argmax(axis=1)

    # Create 7 dummies (one-hot on dominant bucket)
    names = [
        "vote",
        "incentives",
        "govcouncil",
        "ecosys",
        "grants",
        "liquidity",
        "treasuryops",
    ]
    for i, name in enumerate(names):
        doc_topics_df[f"d_{name}"] = (bucket_argmax == i).astype(int)

    # only keep the id + dummy
    doc_topics_df = doc_topics_df[[ID_COL] + [f"d_{name}" for name in names]]
    doc_topics_df.to_csv(
        PROCESSED_DATA_DIR / "proposals_adjusted_topics.csv", index=False
    )

    # ---- Persist model + vectorizer ----
    joblib.dump(vectorizer, out_dir / "lda_vectorizer.joblib")
    joblib.dump(lda, out_dir / "lda_model.joblib")

    # ---- Console summary ----
    print(f"[OK] topics.csv -> {out_dir/'topics.csv'}")
    print(f"[OK] doc_topics.csv -> {out_dir/'doc_topics.csv'}")
    print("Top words per topic:")
    for k in range(min(N_TOPICS, 10)):
        words, _ = top_words_for_topic(lda.components_[k], vocab, n_top=10)
        print(f"  Topic {k:02d}: {', '.join(words)}")
