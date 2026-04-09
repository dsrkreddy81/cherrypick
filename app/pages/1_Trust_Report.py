import streamlit as st

st.set_page_config(page_title="Trust Report — Cherry Pick", page_icon="🍒", layout="wide")

if "report" not in st.session_state:
    st.warning("No analysis yet. Go to the main page and analyze a business first.")
    st.stop()

report = st.session_state["report"]
business = st.session_state["business"]
reviews = st.session_state["reviews"]

st.title(f"Trust Report: {business['name']}")
if business.get("address"):
    st.caption(business["address"])
if business.get("category"):
    st.caption(f"Category: {business['category']}")

col1, col2, col3 = st.columns(3)

trust_score = report["trust_score"]
if trust_score >= 80:
    score_color = "🟢"
elif trust_score >= 50:
    score_color = "🟡"
else:
    score_color = "🔴"

col1.metric("Trust Score", f"{score_color} {trust_score}/100")
col2.metric("Google Rating", f"⭐ {business.get('google_rating', 'N/A')}")
col3.metric("Cherry Pick Rating", f"⭐ {report['adjusted_rating']}")

if report["red_flags"]:
    st.subheader("🚩 Red Flags")
    for flag in report["red_flags"]:
        st.markdown(f"- {flag}")

stats = report.get("summary_stats", {})
if stats:
    st.subheader("📊 Summary")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total Reviews", stats.get("total_reviews", 0))
    c2.metric("Genuine", f"{stats.get('genuine_pct', 0)}%")
    c3.metric("Suspicious", f"{stats.get('suspicious_pct', 0)}%")
    c4.metric("Likely Fake", f"{stats.get('fake_pct', 0)}%")

st.subheader("📝 Review Analysis")

review_lookup = {r["id"]: r for r in reviews}

for analysis in report.get("review_analyses", []):
    rid = analysis["review_id"]
    review = review_lookup.get(rid, {})
    classification = analysis["classification"]

    if classification == "genuine":
        color = "🟢"
    elif classification == "suspicious":
        color = "🟡"
    else:
        color = "🔴"

    stars = "⭐" * analysis.get("star_rating", 0)
    reviewer = review.get("reviewer_name", "Anonymous")
    date = review.get("review_date", "")

    with st.expander(f"{color} {stars} — {reviewer} ({date})"):
        st.write(review.get("review_text", ""))
        st.caption(f"**Classification:** {classification} | **Score:** {analysis['combined_score']:.2f}")

        h = analysis.get("heuristic_scores", {})
        if h:
            st.caption(
                f"Timing: {h.get('timing', 0):.2f} | "
                f"Rating dist: {h.get('rating_dist', 0):.2f} | "
                f"Single-review: {h.get('single_review', 0):.2f} | "
                f"Text similarity: {h.get('text_similarity', 0):.2f} | "
                f"Text quality: {h.get('text_quality', 0):.2f} | "
                f"Sentiment: {h.get('sentiment_mismatch', 0):.2f}"
            )

        if analysis.get("claude_reasoning"):
            st.caption(f"**Claude says:** {analysis['claude_reasoning']}")
