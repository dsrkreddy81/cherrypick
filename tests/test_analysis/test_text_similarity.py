from cherrypick.analysis.heuristics.text_similarity import score_text_similarity

def test_unique_reviews_low_score():
    reviews = [
        "The pasta here is incredible, especially the carbonara",
        "Waited 45 minutes for a table but the steak was worth it",
        "My kids loved the playground area, very family friendly",
    ]
    scores = score_text_similarity(reviews)
    assert all(s < 0.3 for s in scores)

def test_duplicate_reviews_high_score():
    reviews = [
        "Great place highly recommend!",
        "Great place highly recommend!",
        "Great place highly recommend!",
        "The carbonara was fantastic, best I've had in town",
    ]
    scores = score_text_similarity(reviews)
    assert scores[0] > 0.7
    assert scores[3] < 0.3

def test_empty():
    assert score_text_similarity([]) == []

def test_single_review():
    assert score_text_similarity(["Just one review"]) == [0.0]
