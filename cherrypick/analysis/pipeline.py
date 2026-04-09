from cherrypick.analysis.heuristics.combined import compute_heuristic_scores
from cherrypick.analysis.llm.claude_analyzer import analyze_reviews_with_claude
from cherrypick.scoring.trust_score import compute_trust_report

SUSPICION_THRESHOLD = 0.35
FAKE_THRESHOLD = 0.6
SUSPICIOUS_THRESHOLD = 0.3


def analyze_business(
    reviews: list[dict],
    business_name: str,
    business_category: str | None,
    google_rating: float,
    skip_claude: bool = False,
) -> dict:
    if not reviews:
        report = compute_trust_report([], google_rating)
        report["review_analyses"] = []
        return report

    heuristic_results = compute_heuristic_scores(reviews)

    claude_results = {}
    if not skip_claude:
        flagged = [
            {"id": r["id"], "text": r["review_text"], "star_rating": r["star_rating"]}
            for r, h in zip(reviews, heuristic_results)
            if h.combined_score >= SUSPICION_THRESHOLD
        ]
        if flagged:
            claude_raw = analyze_reviews_with_claude(
                business_name=business_name,
                business_category=business_category,
                reviews=flagged,
            )
            for cr in claude_raw:
                claude_results[cr["review_id"]] = cr

    review_analyses = []
    for review, heuristic in zip(reviews, heuristic_results):
        rid = review["id"]
        claude = claude_results.get(rid)

        if claude:
            final_score = 0.5 * heuristic.combined_score + 0.5 * claude["fake_probability"]
            claude_prob = claude["fake_probability"]
            claude_reason = claude["reasoning"]
        else:
            final_score = heuristic.combined_score
            claude_prob = None
            claude_reason = None

        if final_score >= FAKE_THRESHOLD:
            classification = "likely_fake"
        elif final_score >= SUSPICIOUS_THRESHOLD:
            classification = "suspicious"
        else:
            classification = "genuine"

        review_analyses.append({
            "review_id": rid,
            "combined_score": round(final_score, 3),
            "classification": classification,
            "star_rating": review["star_rating"],
            "heuristic_scores": {
                "timing": heuristic.timing_score,
                "rating_dist": heuristic.rating_dist_score,
                "single_review": heuristic.single_review_score,
                "text_similarity": heuristic.text_similarity_score,
                "text_quality": heuristic.text_quality_score,
                "sentiment_mismatch": heuristic.sentiment_mismatch_score,
            },
            "claude_fake_probability": claude_prob,
            "claude_reasoning": claude_reason,
        })

    report = compute_trust_report(review_analyses, google_rating)
    report["review_analyses"] = review_analyses
    return report
