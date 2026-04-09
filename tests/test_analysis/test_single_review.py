from cherrypick.analysis.heuristics.single_review import score_single_review_accounts


def test_established_reviewer_low_score():
    scores = score_single_review_accounts([50, 30, 100])
    assert all(s < 0.2 for s in scores)


def test_single_review_high_score():
    scores = score_single_review_accounts([1, 1, 1])
    assert all(s > 0.7 for s in scores)


def test_mixed():
    scores = score_single_review_accounts([1, 50, 2, 100])
    assert scores[0] > scores[1]
    assert scores[2] > scores[3]
