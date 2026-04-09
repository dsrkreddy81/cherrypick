from cherrypick.analysis.heuristics.sentiment import score_sentiment_mismatch

def test_positive_text_high_rating_low_score():
    score = score_sentiment_mismatch(5, "Absolutely wonderful food, best experience ever!")
    assert score < 0.2

def test_negative_text_high_rating_high_score():
    score = score_sentiment_mismatch(5, "Terrible service, food was cold, waited an hour. Disgusting.")
    assert score > 0.5

def test_positive_text_low_rating_high_score():
    score = score_sentiment_mismatch(1, "Great food, amazing service, loved every minute!")
    assert score > 0.5

def test_empty_text():
    score = score_sentiment_mismatch(5, "")
    assert score == 0.0
