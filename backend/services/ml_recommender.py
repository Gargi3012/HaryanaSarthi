import pandas as pd
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity


def safe_num(value, default=0.0):
    try:
        return float(value)
    except Exception:
        return default


def encode_text(value: str, bucket: int = 100):
    value = str(value).strip().lower()
    return abs(hash(value)) % bucket


def similarity_rank(df: pd.DataFrame, feature_rows: list, user_vector: list, top_n: int = 10):
    if df.empty:
        return df

    matrix = np.array(feature_rows, dtype=float)
    user = np.array([user_vector], dtype=float)

    scores = cosine_similarity(user, matrix)[0]
    ranked_df = df.copy()
    ranked_df["ml_score"] = scores
    ranked_df = ranked_df.sort_values(by="ml_score", ascending=False)
    return ranked_df.head(top_n)