from pathlib import Path
import re
import pandas as pd

BASE_DIR = Path(__file__).resolve().parent.parent
DICTIONARY_PATH = BASE_DIR / "data" / "dictionaries" / "Loughran-McDonald_MasterDictionary_1993-2025.csv"


def load_lm_dictionary(file_path=DICTIONARY_PATH):
    return pd.read_csv(file_path)


def build_sentiment_sets(lm_df):
    positive_words = set(
        lm_df.loc[lm_df["Positive"] > 0, "Word"].str.lower()
    )
    negative_words = set(
        lm_df.loc[lm_df["Negative"] > 0, "Word"].str.lower()
    )
    return positive_words, negative_words


def tokenize(text):
    return re.findall(r"\b[a-z]+\b", text.lower())


def compute_sentiment(text, positive_words, negative_words):
    words = tokenize(text)

    pos_count = sum(1 for w in words if w in positive_words)
    neg_count = sum(1 for w in words if w in negative_words)

    pos_norm = pos_count / len(positive_words)
    neg_norm = neg_count / len(negative_words)

    if (pos_norm + neg_norm) == 0:
        return 0

    return (pos_norm - neg_norm) / (pos_norm + neg_norm)


def compute_sentiment_by_year(records):
    lm_df = load_lm_dictionary()
    positive_words, negative_words = build_sentiment_sets(lm_df)

    records = sorted(records, key=lambda x: x["year"])

    results = []

    for record in records:
        sentiment = compute_sentiment(
            record["text"],
            positive_words,
            negative_words
        )

        results.append({
            "ticker": record["ticker"],
            "year": record["year"],
            "sentiment": sentiment
        })

    return results