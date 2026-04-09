import json
import pytest
from unittest.mock import patch, MagicMock
from cherrypick.analysis.llm.claude_analyzer import analyze_reviews_with_claude, build_prompt


def test_build_prompt_includes_business_context():
    reviews = [
        {"id": 1, "text": "Great place!", "star_rating": 5},
        {"id": 2, "text": "Terrible food", "star_rating": 1},
    ]
    prompt = build_prompt("Joe's Pizza", "Restaurant", reviews)
    assert "Joe's Pizza" in prompt
    assert "Restaurant" in prompt
    assert "Great place!" in prompt
    assert "Terrible food" in prompt


def test_analyze_returns_results_per_review():
    mock_response = MagicMock()
    mock_response.content = [MagicMock(text=json.dumps([
        {"review_id": 1, "fake_probability": 0.8, "reasoning": "Generic text, no specifics"},
        {"review_id": 2, "fake_probability": 0.1, "reasoning": "Specific negative experience"},
    ]))]
    with patch("cherrypick.analysis.llm.claude_analyzer.get_client") as mock_client:
        mock_client.return_value.messages.create.return_value = mock_response
        results = analyze_reviews_with_claude(
            business_name="Joe's Pizza",
            business_category="Restaurant",
            reviews=[
                {"id": 1, "text": "Great place!", "star_rating": 5},
                {"id": 2, "text": "Terrible food, cold pizza, rude staff", "star_rating": 1},
            ],
        )
    assert len(results) == 2
    assert results[0]["fake_probability"] == 0.8
    assert results[1]["fake_probability"] == 0.1
