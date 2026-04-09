from cherrypick.analysis.heuristics.timing import score_timing_clusters


def test_uniform_reviews_low_score():
    dates = [f"2025-{month:02d}-15" for month in range(1, 13)]
    scores = score_timing_clusters(dates)
    assert all(s < 0.3 for s in scores)


def test_burst_reviews_high_score():
    dates = ["2025-06-15"] * 10 + ["2025-01-01", "2025-12-31"]
    scores = score_timing_clusters(dates)
    burst_scores = scores[:10]
    assert all(s > 0.5 for s in burst_scores)


def test_empty_reviews():
    scores = score_timing_clusters([])
    assert scores == []
