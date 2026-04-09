from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np


def score_text_similarity(review_texts: list[str]) -> list[float]:
    if len(review_texts) <= 1:
        return [0.0] * len(review_texts)
    texts = [t if t.strip() else "empty" for t in review_texts]
    vectorizer = TfidfVectorizer(stop_words="english", max_features=5000)
    tfidf_matrix = vectorizer.fit_transform(texts)
    sim_matrix = cosine_similarity(tfidf_matrix)
    scores = []
    for i in range(len(texts)):
        sims = sim_matrix[i].copy()
        sims[i] = 0
        max_sim = float(np.max(sims))
        top_k = sorted(sims, reverse=True)[:3]
        avg_top = float(np.mean(top_k))
        score = 0.6 * max_sim + 0.4 * avg_top
        scores.append(round(min(1.0, score), 3))
    return scores
