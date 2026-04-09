from datetime import datetime, timedelta
from unittest.mock import AsyncMock, patch
from cherrypick.db.session import get_engine, create_tables, get_session
from cherrypick.db.models import Business, Review
from cherrypick.scraper.pipeline import scrape_and_store, get_cached_business


def setup_module():
    engine = get_engine()
    create_tables(engine)


def test_get_cached_business_returns_none_for_unknown():
    result = get_cached_business("https://maps.google.com/place/nonexistent_test_xyz")
    assert result is None


def test_get_cached_business_returns_fresh_data():
    session = get_session()
    biz = Business(
        place_id="test_cache_fresh_123",
        name="Test Business Fresh",
        google_maps_url="https://maps.google.com/place/test_fresh_unique",
        scraped_at=datetime.utcnow(),
    )
    session.add(biz)
    session.commit()
    biz_id = biz.id

    result = get_cached_business("https://maps.google.com/place/test_fresh_unique")
    assert result is not None
    assert result.name == "Test Business Fresh"

    session.delete(session.get(Business, biz_id))
    session.commit()
    session.close()


def test_get_cached_business_returns_none_for_stale_data():
    session = get_session()
    biz = Business(
        place_id="stale_place_test",
        name="Stale Business",
        google_maps_url="https://maps.google.com/place/stale_test_unique",
        scraped_at=datetime.utcnow() - timedelta(days=10),
    )
    session.add(biz)
    session.commit()
    biz_id = biz.id

    result = get_cached_business(
        "https://maps.google.com/place/stale_test_unique", max_age_days=7
    )
    assert result is None

    session.delete(session.get(Business, biz_id))
    session.commit()
    session.close()
