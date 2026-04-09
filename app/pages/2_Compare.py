import streamlit as st
from dotenv import load_dotenv

load_dotenv()

st.set_page_config(page_title="Compare — Cherry Pick", page_icon="🍒", layout="wide")
st.title("🍒 Compare Businesses")

st.write("Enter 2-3 Google Maps URLs or business names to compare side by side.")

urls = []
for i in range(3):
    label = f"Business {i + 1}" + (" (optional)" if i == 2 else "")
    url = st.text_input(label, key=f"compare_url_{i}")
    if url:
        urls.append(url)

if st.button("Compare", type="primary", disabled=len(urls) < 2):
    from cherrypick.scraper.pipeline import scrape_and_store, get_cached_business
    from cherrypick.analysis.pipeline import analyze_business
    from cherrypick.db.session import get_session
    from cherrypick.db.models import Review

    reports = []
    businesses = []

    for url in urls:
        cached = get_cached_business(url)
        if cached:
            biz = cached
        else:
            with st.spinner(f"Scraping {url}..."):
                biz = scrape_and_store(url)

        session = get_session()
        db_reviews = session.query(Review).filter_by(business_id=biz.id).all()
        reviews_list = [
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

        with st.spinner(f"Analyzing {biz.name}..."):
            report = analyze_business(
                reviews=reviews_list,
                business_name=biz.name,
                business_category=biz.category,
                google_rating=biz.google_rating or 0.0,
            )

        reports.append(report)
        businesses.append(biz)

    cols = st.columns(len(reports))
    for col, report, biz in zip(cols, reports, businesses):
        score = report["trust_score"]
        if score >= 80:
            emoji = "🟢"
        elif score >= 50:
            emoji = "🟡"
        else:
            emoji = "🔴"

        with col:
            st.subheader(biz.name)
            st.metric("Trust Score", f"{emoji} {score}/100")
            st.metric("Google Rating", f"⭐ {biz.google_rating or 'N/A'}")
            st.metric("Cherry Pick Rating", f"⭐ {report['adjusted_rating']}")

            stats = report.get("summary_stats", {})
            st.caption(f"Reviews: {stats.get('total_reviews', 0)}")
            st.caption(f"Genuine: {stats.get('genuine_pct', 0)}%")
            st.caption(f"Suspicious: {stats.get('suspicious_pct', 0)}%")
            st.caption(f"Likely Fake: {stats.get('fake_pct', 0)}%")

            if report["red_flags"]:
                st.markdown("**Red Flags:**")
                for flag in report["red_flags"]:
                    st.markdown(f"- {flag}")
