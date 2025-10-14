#!/usr/bin/env python3
"""Script to implement LDA topic modeling on proposal texts (simple, no argparse).
Adds 5 bucket dummies and bucket shares based on 6-topic LDA."""

import re
import string
import joblib
import numpy as np
import pandas as pd

from pathlib import Path
from sklearn.decomposition import LatentDirichletAllocation
from sklearn.feature_extraction.text import CountVectorizer, ENGLISH_STOP_WORDS

# ========= Config (edit as needed) =========
from governenv.constants import PROCESSED_DATA_DIR, EVENT_WINDOW

INPUT_CSV = f"{PROCESSED_DATA_DIR}/event_study_panel_created.csv"  # must have columns: id, body, index
ID_COL = "id"
TEXT_COL = "body"
OUT_DIR = f"{PROCESSED_DATA_DIR}/lda_body"

N_TOPICS = 6
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
    idx = np.argsort(components_row)[::-1][:n_top]
    words = [feature_names[i] for i in idx]
    weights = [components_row[i] for i in idx]
    return words, weights


def row_entropy(p: np.ndarray) -> float:
    p_safe = np.clip(p, 1e-12, 1.0)
    return float(-(p_safe * np.log(p_safe)).sum())


if __name__ == "__main__":
    out_dir = Path(OUT_DIR)
    out_dir.mkdir(parents=True, exist_ok=True)

    # ---- Load + restrict to one row per proposal (index == EVENT_WINDOW) ----
    df = pd.read_csv(INPUT_CSV)
    if "index" not in df.columns:
        raise ValueError(
            "INPUT_CSV must include an 'index' column (event-study index)."
        )
    df = df.loc[df["index"] == EVENT_WINDOW].copy()

    if ID_COL not in df.columns or TEXT_COL not in df.columns:
        raise ValueError(f"Input CSV must have columns '{ID_COL}' and '{TEXT_COL}'.")

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
    topics_df.to_csv(out_dir / "topics.csv", index=False)

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

    # ---- Build 5 bucket shares from 6 topics (mapping based on your interpretation) ----
    # Buckets:
    #   Budget            = topic_0
    #   Dev/Integrations  = topic_1 + topic_2
    #   Governance/Grants = topic_3
    #   Incentives        = topic_4
    #   Liquidity/Treasury= topic_5
    doc_topics_df["bucket_budget_share"] = doc_topics_df.get("topic_0", 0.0)
    doc_topics_df["bucket_devint_share"] = doc_topics_df.get(
        "topic_1", 0.0
    ) + doc_topics_df.get("topic_2", 0.0)
    doc_topics_df["bucket_govgrants_share"] = doc_topics_df.get("topic_3", 0.0)
    doc_topics_df["bucket_incentives_share"] = doc_topics_df.get("topic_4", 0.0)
    doc_topics_df["bucket_liqtreasury_share"] = doc_topics_df.get("topic_5", 0.0)

    bucket_cols = [
        "bucket_budget_share",
        "bucket_devint_share",
        "bucket_govgrants_share",
        "bucket_incentives_share",
        "bucket_liqtreasury_share",
    ]
    # Dominant bucket index 0..4
    bucket_argmax = np.asarray(doc_topics_df[bucket_cols].values).argmax(axis=1)

    # Create 5 dummies (one-hot on dominant bucket)
    names = ["budget", "devint", "govgrants", "incentives", "liqtreasury"]
    for i, name in enumerate(names):
        doc_topics_df[f"d_{name}"] = (bucket_argmax == i).astype(int)

    # Save per-doc topics with bucket shares + dummies
    doc_topics_df.to_csv(out_dir / "doc_topics.csv", index=False)

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

    # ---- Merge topic features back to event-study panels (created & end) ----
    panel_created = pd.read_csv(
        Path(PROCESSED_DATA_DIR) / "event_study_panel_created.csv"
    )
    panel_end = pd.read_csv(Path(PROCESSED_DATA_DIR) / "event_study_panel_end.csv")

    created_enriched = panel_created.merge(doc_topics_df, on=ID_COL, how="left").drop(
        columns=["body"], errors="ignore"
    )
    end_enriched = panel_end.merge(doc_topics_df, on=ID_COL, how="left").drop(
        columns=["body"], errors="ignore"
    )

    created_out = Path(PROCESSED_DATA_DIR) / "event_study_panel_created_topics.csv"
    end_out = Path(PROCESSED_DATA_DIR) / "event_study_panel_end_topics.csv"

    created_enriched.to_csv(created_out, index=False)
    end_enriched.to_csv(end_out, index=False)

    print(f"[OK] merged created panel -> {created_out}")
    print(f"[OK] merged end panel     -> {end_out}")
