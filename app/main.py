import streamlit as st
import asyncio
import sys
import threading
from dotenv import load_dotenv


def run_async(coro):
    """Run an async coroutine from Streamlit (which has its own event loop).
    Playwright needs ProactorEventLoop on Windows for subprocess support."""
    result = None
    exception = None

    def _run():
        nonlocal result, exception
        try:
            if sys.platform == "win32":
                asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                result = loop.run_until_complete(coro)
            finally:
                loop.close()
        except Exception as e:
            exception = e

    thread = threading.Thread(target=_run)
    thread.start()
    thread.join()

    if exception:
        raise exception
    return result

load_dotenv()

st.set_page_config(page_title="Cherry Pick", page_icon="🍒", layout="wide")

st.title("🍒 Cherry Pick")
st.subheader("Before you trust any business, Cherry Pick it.")

url = st.text_input(
    "Paste a Google Maps link",
    placeholder="https://www.google.com/maps/place/...",
)

if st.button("Analyze", type="primary", disabled=not url):
    from cherrypick.scraper.url_parser import parse_google_maps_url
    from cherrypick.scraper.pipeline import scrape_and_store, get_cached_business
    from cherrypick.analysis.pipeline import analyze_business
    from cherrypick.db.session import get_session
    from cherrypick.db.models import Review

    try:
        parse_google_maps_url(url)
    except ValueError as e:
        st.error(str(e))
        st.stop()

    with st.spinner("Checking cache..."):
        cached = get_cached_business(url)

    if cached:
        st.info(f"Found cached data for **{cached.name}** (scraped {cached.scraped_at.strftime('%Y-%m-%d')})")
        biz = cached
    else:
        with st.spinner("Scraping reviews from Google Maps... This may take a few minutes."):
            biz = run_async(scrape_and_store(url))
        st.success(f"Scraped **{biz.name}** successfully!")

    session = get_session()
    db_reviews = session.query(Review).filter_by(business_id=biz.id).all()
    reviews = [
        {
            "id": r.id,
            "review_text": r.review_text or "",
            "star_rating": r.star_rating,
            "review_date": r.review_date or "",
            "reviewer_total_reviews": r.reviewer_total_reviews or 1,
            "reviewer_name": r.reviewer_name,
        }
        for r in db_reviews
    ]
    session.close()

    with st.spinner("Running analysis..."):
        report = analyze_business(
            reviews=reviews,
            business_name=biz.name,
            business_category=biz.category,
            google_rating=biz.google_rating or 0.0,
        )

    st.session_state["report"] = report
    st.session_state["business"] = {
        "name": biz.name,
        "address": biz.address,
        "category": biz.category,
        "google_rating": biz.google_rating,
    }
    st.session_state["reviews"] = reviews

    st.success("Analysis complete! Go to **Trust Report** page to see results.")
