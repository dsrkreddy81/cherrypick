from nltk.sentiment import SentimentIntensityAnalyzer

_sia = None


def _get_analyzer() -> SentimentIntensityAnalyzer:
    global _sia
    if _sia is None:
        _sia = SentimentIntensityAnalyzer()
    return _sia


def score_sentiment_mismatch(star_rating: int, review_text: str) -> float:
    if not review_text or not review_text.strip():
        return 0.0
    sia = _get_analyzer()
    sentiment = sia.polarity_scores(review_text)
    compound = sentiment["compound"]
    expected = (star_rating - 3) / 2.5
    mismatch = abs(compound - expected)
    score = max(0.0, (mismatch - 0.4) / 0.8)
    return round(min(1.0, score), 3)
