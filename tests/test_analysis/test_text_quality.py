from cherrypick.analysis.heuristics.text_quality import score_text_quality

def test_detailed_review_low_score():
    text = (
        "We visited last Saturday for my wife's birthday. The host Sarah seated us "
        "at a corner table with a nice view of the garden. I had the ribeye ($42) "
        "which was perfectly medium-rare. My wife loved the lobster risotto. "
        "Only downside was the 20 minute wait for dessert."
    )
    score = score_text_quality(text)
    assert score < 0.3

def test_generic_review_high_score():
    score = score_text_quality("Great place highly recommend!")
    assert score > 0.5

def test_empty_review_high_score():
    score = score_text_quality("")
    assert score > 0.7

def test_very_short_review():
    score = score_text_quality("Nice")
    assert score > 0.5
