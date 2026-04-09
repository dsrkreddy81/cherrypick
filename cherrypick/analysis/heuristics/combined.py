from dataclasses import dataclass

from cherrypick.analysis.heuristics.timing import score_timing_clusters
from cherrypick.analysis.heuristics.rating_dist import score_rating_distribution
from cherrypick.analysis.heuristics.single_review import score_single_review_accounts
from cherrypick.analysis.heuristics.text_similarity import score_text_similarity
from cherrypick.analysis.heuristics.text_quality import score_text_quality
from cherrypick.analysis.heuristics.sentiment import score_sentiment_mismatch

WEIGHTS = {
    "timing": 0.20,
    "rating_dist": 0.10,
    "single_review": 0.20,
    "text_similarity": 0.20,
    "text_quality": 0.15,
    "sentiment_mismatch": 0.15,
}


@dataclass
class HeuristicResult:
    timing_score: float
    rating_dist_score: float
    single_review_score: float
    text_similarity_score: float
    text_quality_score: float
    sentiment_mismatch_score: float
    combined_score: float


def compute_heuristic_scores(reviews: list[dict]) -> list[HeuristicResult]:
    if not reviews:
        return []

    dates = [r.get("review_date", "") for r in reviews]
    ratings = [r.get("star_rating", 0) for r in reviews]
    texts = [r.get("review_text", "") for r in reviews]
    reviewer_counts = [r.get("reviewer_total_reviews", 1) for r in reviews]

    timing_scores = score_timing_clusters(dates)
    rating_dist = score_rating_distribution(ratings)
    single_review_scores = score_single_review_accounts(reviewer_counts)
    similarity_scores = score_text_similarity(texts)

    results = []
    for i, review in enumerate(reviews):
        text_qual = score_text_quality(review.get("review_text", ""))
        sentiment = score_sentiment_mismatch(
            review.get("star_rating", 0),
            review.get("review_text", ""),
        )
        scores = {
            "timing": timing_scores[i],
            "rating_dist": rating_dist,
            "single_review": single_review_scores[i],
            "text_similarity": similarity_scores[i],
            "text_quality": text_qual,
            "sentiment_mismatch": sentiment,
        }
        combined = sum(scores[k] * WEIGHTS[k] for k in WEIGHTS)
        results.append(HeuristicResult(
            timing_score=scores["timing"],
            rating_dist_score=scores["rating_dist"],
            single_review_score=scores["single_review"],
            text_similarity_score=scores["text_similarity"],
            text_quality_score=scores["text_quality"],
            sentiment_mismatch_score=scores["sentiment_mismatch"],
            combined_score=round(combined, 3),
        ))
    return results
