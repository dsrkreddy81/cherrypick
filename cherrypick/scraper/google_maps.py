"""Google Maps review scraper using gosom/google-maps-scraper via Docker.

Runs the gosom/google-maps-scraper Docker container with a search query,
reads the JSON output, and returns structured review data.
"""

import json
import os
import subprocess
import tempfile
import uuid


async def scrape_reviews(url: str, max_reviews: int = 500) -> dict:
    """Scrape reviews from a Google Maps business.

    Args:
        url: Google Maps URL or business search query (e.g. "E Sushi Indianapolis").
        max_reviews: Maximum reviews to collect (gosom caps at ~300 with -extra-reviews).

    Returns:
        Dict with business_name, business_address, business_category,
        google_rating, total_review_count, reviews (list of dicts).
    """
    # Extract a search query from the URL or use it directly
    query = _url_to_query(url)
    return _run_gosom_scraper(query)


def scrape_reviews_sync(url: str, max_reviews: int = 500) -> dict:
    """Synchronous version of scrape_reviews."""
    query = _url_to_query(url)
    return _run_gosom_scraper(query)


def _url_to_query(url: str) -> str:
    """Convert a Google Maps URL to a search query, or pass through if already a query."""
    import re
    from urllib.parse import unquote

    # If it's not a URL, use it as-is (it's already a search query)
    if not url.startswith("http"):
        return url

    # Try to extract place name from /place/Name+Here/ pattern
    match = re.search(r"/place/([^/@]+)", url)
    if match:
        return unquote(match.group(1)).replace("+", " ")

    # For short URLs or other formats, use the full URL as query
    # gosom scraper can handle URLs too
    return url


def _run_gosom_scraper(query: str) -> dict:
    """Run the gosom/google-maps-scraper Docker container and parse output."""
    run_id = uuid.uuid4().hex[:8]

    # Use a temp directory for input/output
    with tempfile.TemporaryDirectory() as tmpdir:
        # Write query file
        query_file = os.path.join(tmpdir, "queries.txt")
        with open(query_file, "w", encoding="utf-8") as f:
            f.write(query + "\n")

        output_file = os.path.join(tmpdir, "results.json")

        # Convert Windows paths to Docker-compatible paths
        tmpdir_docker = tmpdir.replace("\\", "/")
        if tmpdir_docker[1] == ":":
            # C:/Users/... -> /c/Users/...
            tmpdir_docker = "/" + tmpdir_docker[0].lower() + tmpdir_docker[2:]

        cmd = [
            "docker", "run", "--rm",
            "-v", f"{tmpdir_docker}/queries.txt:/queries.txt",
            "-v", f"{tmpdir_docker}:/results",
            "gosom/google-maps-scraper",
            "-input", "/queries.txt",
            "-results", "/results/results.json",
            "-json",
            "-depth", "1",
            "-exit-on-inactivity", "3m",
        ]

        # Set MSYS_NO_PATHCONV to prevent Git Bash path mangling
        env = os.environ.copy()
        env["MSYS_NO_PATHCONV"] = "1"

        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=300,
            env=env,
        )

        if result.returncode != 0 and not os.path.exists(output_file):
            raise RuntimeError(
                f"gosom scraper failed (exit {result.returncode}): {result.stderr[-500:]}"
            )

        # Parse output
        if not os.path.exists(output_file):
            raise RuntimeError("Scraper produced no output file")

        with open(output_file, "r", encoding="utf-8") as f:
            data = json.load(f)

    return _parse_gosom_output(data)


def _parse_gosom_output(data: dict | list) -> dict:
    """Convert gosom JSON output to our standard format."""
    # If it's a list, take the first result
    if isinstance(data, list):
        if not data:
            raise RuntimeError("Scraper returned empty results")
        data = data[0]

    # Extract business metadata
    business_name = data.get("title")
    business_address = data.get("address")
    categories = data.get("categories", [])
    business_category = categories[0] if categories else data.get("category")
    google_rating = data.get("review_rating")
    total_review_count = data.get("review_count", 0)

    # Extract reviews
    reviews = []
    raw_reviews = data.get("user_reviews") or []

    # Also check user_reviews_extended if available (from -extra-reviews flag)
    extended = data.get("user_reviews_extended") or []
    if extended:
        raw_reviews = extended

    for r in raw_reviews:
        reviews.append({
            "reviewer_name": r.get("Name"),
            "star_rating": r.get("Rating", 0),
            "review_text": r.get("Description", ""),
            "review_date": r.get("When", ""),
            "reviewer_total_reviews": r.get("ReviewCount", 1),
            "photo_count": len(r.get("Images") or []),
        })

    return {
        "business_name": business_name,
        "business_address": business_address,
        "business_category": business_category,
        "google_rating": google_rating,
        "total_review_count": total_review_count,
        "reviews_per_rating": data.get("reviews_per_rating"),
        "reviews": reviews,
    }
