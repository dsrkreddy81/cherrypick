from cherrypick.analysis.heuristics.combined import compute_heuristic_scores, HeuristicResult


def _make_reviews():
    return [
        {
            "review_text": "Great place highly recommend!",
            "star_rating": 5,
            "review_date": "2025-06-15",
            "reviewer_total_reviews": 1,
        },
        {
            "review_text": "We celebrated our anniversary here. The filet mignon was perfectly cooked, and our server Mike was attentive without being intrusive. The creme brulee was a perfect finish.",
            "star_rating": 4,
            "review_date": "2025-03-10",
            "reviewer_total_reviews": 47,
        },
    ]


def test_compute_returns_results_for_each_review():
    reviews = _make_reviews()
    results = compute_heuristic_scores(reviews)
    assert len(results) == 2
    assert isinstance(results[0], HeuristicResult)


def test_generic_single_review_account_more_suspicious():
    reviews = _make_reviews()
    results = compute_heuristic_scores(reviews)
    assert results[0].combined_score > results[1].combined_score


def test_result_has_all_fields():
    reviews = _make_reviews()
    results = compute_heuristic_scores(reviews)
    r = results[0]
    assert 0.0 <= r.timing_score <= 1.0
    assert 0.0 <= r.rating_dist_score <= 1.0
    assert 0.0 <= r.single_review_score <= 1.0
    assert 0.0 <= r.text_similarity_score <= 1.0
    assert 0.0 <= r.text_quality_score <= 1.0
    assert 0.0 <= r.sentiment_mismatch_score <= 1.0
    assert 0.0 <= r.combined_score <= 1.0
