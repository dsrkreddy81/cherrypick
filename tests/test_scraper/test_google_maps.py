import pytest
import asyncio
from cherrypick.scraper.google_maps import scrape_reviews

TEST_URL = "https://www.google.com/maps/place/Statue+of+Liberty"


@pytest.mark.integration
@pytest.mark.asyncio
async def test_scrape_reviews_returns_data():
    result = await scrape_reviews(TEST_URL, max_reviews=10)
    assert result["business_name"] is not None
    assert len(result["reviews"]) > 0
    first_review = result["reviews"][0]
    assert "reviewer_name" in first_review
    assert "star_rating" in first_review
    assert "review_text" in first_review
