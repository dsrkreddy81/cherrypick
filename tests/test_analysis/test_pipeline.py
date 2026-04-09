import pytest
from unittest.mock import patch
from cherrypick.analysis.pipeline import analyze_business, SUSPICION_THRESHOLD


def _make_db_reviews():
    return [
        {
            "id": 1,
            "review_text": "Great place highly recommend!",
            "star_rating": 5,
            "review_date": "2025-06-15",
            "reviewer_total_reviews": 1,
        },
        {
            "id": 2,
            "review_text": "We visited for our anniversary. The filet was perfect and our server Mike was wonderful.",
            "star_rating": 4,
            "review_date": "2025-03-10",
            "reviewer_total_reviews": 47,
        },
    ]


def test_analyze_business_returns_report():
    mock_claude = [
        {"review_id": 1, "fake_probability": 0.7, "reasoning": "Generic text"},
    ]
    with patch("cherrypick.analysis.pipeline.analyze_reviews_with_claude", return_value=mock_claude):
        report = analyze_business(
            reviews=_make_db_reviews(),
            business_name="Test Place",
            business_category="Restaurant",
            google_rating=4.3,
        )
    assert "trust_score" in report
    assert "adjusted_rating" in report
    assert "red_flags" in report
    assert "review_analyses" in report
    assert len(report["review_analyses"]) == 2


def test_analyze_business_skip_claude():
    report = analyze_business(
        reviews=_make_db_reviews(),
        business_name="Test Place",
        business_category="Restaurant",
        google_rating=4.3,
        skip_claude=True,
    )
    assert "trust_score" in report
    assert len(report["review_analyses"]) == 2
    # All Claude fields should be None when skipped
    for ra in report["review_analyses"]:
        assert ra["claude_fake_probability"] is None
