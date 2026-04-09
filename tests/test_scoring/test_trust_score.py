from cherrypick.scoring.trust_score import compute_trust_report


def _make_analysis_results():
    return [
        {"combined_score": 0.1, "classification": "genuine", "star_rating": 4},
        {"combined_score": 0.15, "classification": "genuine", "star_rating": 5},
        {"combined_score": 0.2, "classification": "genuine", "star_rating": 3},
        {"combined_score": 0.6, "classification": "suspicious", "star_rating": 5},
        {"combined_score": 0.7, "classification": "suspicious", "star_rating": 5},
        {"combined_score": 0.85, "classification": "likely_fake", "star_rating": 5},
    ]


def test_trust_score_range():
    report = compute_trust_report(_make_analysis_results(), google_rating=4.5)
    assert 0 <= report["trust_score"] <= 100


def test_adjusted_rating_excludes_fakes():
    report = compute_trust_report(_make_analysis_results(), google_rating=4.5)
    assert report["adjusted_rating"] < 4.5


def test_red_flags_not_empty():
    report = compute_trust_report(_make_analysis_results(), google_rating=4.5)
    assert len(report["red_flags"]) > 0


def test_all_genuine_high_score():
    results = [
        {"combined_score": 0.1, "classification": "genuine", "star_rating": 4},
        {"combined_score": 0.05, "classification": "genuine", "star_rating": 5},
        {"combined_score": 0.15, "classification": "genuine", "star_rating": 3},
    ]
    report = compute_trust_report(results, google_rating=4.0)
    assert report["trust_score"] >= 80
