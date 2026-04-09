from cherrypick.analysis.heuristics.rating_dist import score_rating_distribution


def test_natural_distribution_low_score():
    ratings = [5, 5, 5, 4, 4, 4, 3, 3, 2, 1]
    score = score_rating_distribution(ratings)
    assert score < 0.3


def test_all_fives_high_score():
    ratings = [5] * 20
    score = score_rating_distribution(ratings)
    assert score > 0.7


def test_j_shaped_high_score():
    ratings = [5] * 40 + [1] * 5 + [3] * 1
    score = score_rating_distribution(ratings)
    assert score > 0.5


def test_empty():
    score = score_rating_distribution([])
    assert score == 0.0
