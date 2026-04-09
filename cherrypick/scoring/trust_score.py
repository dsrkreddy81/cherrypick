def compute_trust_report(analysis_results: list[dict], google_rating: float) -> dict:
    total = len(analysis_results)
    if total == 0:
        return {
            "trust_score": 50,
            "adjusted_rating": google_rating,
            "red_flags": ["No reviews to analyze"],
            "summary_stats": {},
        }

    genuine = [r for r in analysis_results if r["classification"] == "genuine"]
    suspicious = [r for r in analysis_results if r["classification"] == "suspicious"]
    likely_fake = [r for r in analysis_results if r["classification"] == "likely_fake"]

    score = 100.0
    suspicious_pct = len(suspicious) / total
    score -= suspicious_pct * 40
    fake_pct = len(likely_fake) / total
    score -= fake_pct * 70
    avg_combined = sum(r["combined_score"] for r in analysis_results) / total
    score -= avg_combined * 20
    trust_score = max(0, min(100, round(score)))

    genuine_ratings = [r["star_rating"] for r in genuine]
    if genuine_ratings:
        adjusted_rating = round(sum(genuine_ratings) / len(genuine_ratings), 1)
    else:
        adjusted_rating = google_rating

    red_flags = []
    if fake_pct > 0.1:
        red_flags.append(f"{len(likely_fake)} reviews ({fake_pct:.0%}) flagged as likely fake")
    if suspicious_pct > 0.2:
        red_flags.append(f"{len(suspicious)} reviews ({suspicious_pct:.0%}) flagged as suspicious")
    if google_rating and adjusted_rating < google_rating - 0.5:
        red_flags.append(
            f"Adjusted rating ({adjusted_rating}) is significantly lower than Google rating ({google_rating})"
        )

    summary_stats = {
        "total_reviews": total,
        "genuine_count": len(genuine),
        "suspicious_count": len(suspicious),
        "likely_fake_count": len(likely_fake),
        "genuine_pct": round(len(genuine) / total * 100, 1),
        "suspicious_pct": round(suspicious_pct * 100, 1),
        "fake_pct": round(fake_pct * 100, 1),
        "avg_suspicion_score": round(avg_combined, 3),
    }

    return {
        "trust_score": trust_score,
        "adjusted_rating": adjusted_rating,
        "red_flags": red_flags,
        "summary_stats": summary_stats,
    }
