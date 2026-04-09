"""Scraper-to-database pipeline with caching.

Connects the Google Maps scraper to the PostgreSQL database.
Provides caching so we don't re-scrape a business that was
recently scraped (configurable max_age_days, default 7).
"""

import hashlib
from datetime import datetime, timedelta

from cherrypick.db.session import get_session
from cherrypick.db.models import Business, Review
from cherrypick.scraper.google_maps import scrape_reviews, scrape_reviews_sync


def _url_to_place_id(url: str) -> str:
    """Derive a deterministic place_id from a Google Maps URL."""
    return hashlib.sha256(url.encode()).hexdigest()[:32]


def get_cached_business(url: str, max_age_days: int = 7) -> Business | None:
    """Return a cached Business if it was scraped within max_age_days, else None.

    Args:
        url: The Google Maps URL to look up.
        max_age_days: Maximum age in days before data is considered stale.

    Returns:
        Business object if fresh data exists, otherwise None.
    """
    session = get_session()
    try:
        biz = session.query(Business).filter_by(google_maps_url=url).first()
        if biz is None:
            return None
        cutoff = datetime.utcnow() - timedelta(days=max_age_days)
        if biz.scraped_at < cutoff:
            return None
        return biz
    finally:
        session.close()


def scrape_and_store(
    url: str, max_reviews: int = 500, force: bool = False
) -> Business:
    """Scrape reviews from Google Maps and store them in the database.

    Uses caching: if a fresh record exists (scraped within 7 days) and
    force=False, returns the cached Business without re-scraping.

    Args:
        url: Full Google Maps URL or search query for a business.
        max_reviews: Maximum number of reviews to scrape.
        force: If True, always re-scrape regardless of cache.

    Returns:
        The Business ORM object (with reviews committed to DB).
    """
    if not force:
        cached = get_cached_business(url)
        if cached is not None:
            return cached

    data = scrape_reviews_sync(url, max_reviews=max_reviews)

    session = get_session()
    try:
        place_id = _url_to_place_id(url)
        biz = session.query(Business).filter_by(place_id=place_id).first()
        if biz is None:
            biz = Business(place_id=place_id, google_maps_url=url)
            session.add(biz)

        biz.name = data.get("business_name") or "Unknown"
        biz.address = data.get("business_address")
        biz.category = data.get("business_category")
        biz.google_rating = data.get("google_rating")
        biz.total_review_count = data.get("total_review_count")
        biz.scraped_at = datetime.utcnow()

        session.flush()

        # Replace old reviews with freshly scraped ones
        session.query(Review).filter_by(business_id=biz.id).delete()

        for r in data.get("reviews", []):
            review = Review(
                business_id=biz.id,
                reviewer_name=r.get("reviewer_name"),
                reviewer_total_reviews=r.get("reviewer_total_reviews", 1),
                star_rating=r.get("star_rating", 0),
                review_date=r.get("review_date"),
                review_text=r.get("review_text", ""),
                photo_count=r.get("photo_count", 0),
                scraped_at=datetime.utcnow(),
            )
            session.add(review)

        session.commit()
        return biz
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
