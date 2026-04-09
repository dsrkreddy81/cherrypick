"""Google Maps review scraper using Crawl4AI.

Scrapes reviews from a Google Maps business listing by:
1. Loading the page with a headless Chromium browser
2. Clicking the Reviews tab
3. Scrolling the reviews panel to load more reviews
4. Expanding truncated review text
5. Parsing the rendered HTML with BeautifulSoup

CSS selectors are placed in SELECTORS dict at the top for easy updating
when Google changes their DOM structure.
"""

import re

from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig, CacheMode

# ----- CSS selectors (update when Google changes DOM) -----
SELECTORS = {
    "reviews_tab": 'button[aria-label*="Reviews"]',
    "reviews_tab_fallback": 'button[data-tab-index="1"]',
    "review_container": "div.jftiEf",
    "reviewer_name": "div.d4r55",
    "star_rating": "span.kvMYJc",
    "review_text": "span.wiI7pd",
    "review_date": "span.rsqaWe",
    "reviewer_reviews_count": "span.RfnDt",
    "more_button": "button.w8nwRe.kyuRq",
    "scrollable_panel": "div.m6QErb.DxyBCb",
    "scrollable_panel_fallback": 'div.m6QErb[role="feed"]',
    "business_name": "h1.DUGVrf",
    "business_address": 'button[data-item-id="address"]',
    "business_category": 'button[jsaction*="category"]',
    "business_rating": "div.F7nice span[aria-hidden]",
    "total_review_count": 'span[aria-label*="reviews"]',
}


async def scrape_reviews(url: str, max_reviews: int = 500) -> dict:
    """Scrape reviews from a Google Maps business listing.

    Args:
        url: Full Google Maps URL for a business/place.
        max_reviews: Maximum number of reviews to collect (caps scrolling).

    Returns:
        Dict with keys: business_name, business_address, business_category,
        google_rating, total_review_count, reviews (list of dicts).
    """
    browser_config = BrowserConfig(
        browser_type="chromium",
        headless=True,
        extra_args=[
            "--disable-blink-features=AutomationControlled",
            "--disable-features=VizDisplayCompositor",
            "--no-sandbox",
        ],
    )

    scroll_js = _build_scroll_js(max_reviews)

    run_config = CrawlerRunConfig(
        js_code=[scroll_js],
        wait_for=f"css:{SELECTORS['review_container']}",
        cache_mode=CacheMode.BYPASS,
        page_timeout=60000,
        simulate_user=True,
        override_navigator=True,
    )

    async with AsyncWebCrawler(config=browser_config) as crawler:
        result = await crawler.arun(url=url, config=run_config)
        if not result.success:
            raise RuntimeError(f"Failed to crawl {url}: {result.error_message}")

    return _parse_reviews_from_html(result.html)


# ---- JavaScript helpers ----

def _build_scroll_js(max_reviews: int) -> str:
    """Return JS that clicks Reviews tab, expands 'More' buttons, and scrolls the reviews panel."""
    return (
        "(async () => {\n"
        "    // Click Reviews tab\n"
        "    const reviewsTab = document.querySelector('" + SELECTORS["reviews_tab"] + "')\n"
        "        || document.querySelector('" + SELECTORS["reviews_tab_fallback"] + "');\n"
        "    if (reviewsTab) {\n"
        "        reviewsTab.click();\n"
        "        await new Promise(r => setTimeout(r, 3000));\n"
        "    }\n"
        "\n"
        "    // Locate the scrollable reviews panel\n"
        "    const scrollable = document.querySelector('" + SELECTORS["scrollable_panel"] + "')\n"
        "        || document.querySelector('" + SELECTORS["scrollable_panel_fallback"] + "');\n"
        "\n"
        "    if (scrollable) {\n"
        "        let lastCount = 0;\n"
        "        let sameCountStreak = 0;\n"
        "        const maxReviews = " + str(max_reviews) + ";\n"
        "\n"
        "        for (let i = 0; i < 200; i++) {\n"
        "            // Expand truncated reviews\n"
        "            document.querySelectorAll('" + SELECTORS["more_button"] + "').forEach(b => b.click());\n"
        "\n"
        "            scrollable.scrollTop = scrollable.scrollHeight;\n"
        "            await new Promise(r => setTimeout(r, 1500 + Math.random() * 2000));\n"
        "\n"
        "            const count = document.querySelectorAll('" + SELECTORS["review_container"] + "').length;\n"
        "            if (maxReviews > 0 && count >= maxReviews) break;\n"
        "            if (count === lastCount) {\n"
        "                sameCountStreak++;\n"
        "                if (sameCountStreak >= 3) break;\n"
        "            } else {\n"
        "                sameCountStreak = 0;\n"
        "            }\n"
        "            lastCount = count;\n"
        "        }\n"
        "        // Final expand of truncated reviews\n"
        "        document.querySelectorAll('" + SELECTORS["more_button"] + "').forEach(b => b.click());\n"
        "        await new Promise(r => setTimeout(r, 1000));\n"
        "    }\n"
        "})();"
    )


# ---- HTML parsers ----

def _parse_reviews_from_html(html: str) -> dict:
    """Parse review data from the scraped HTML.

    Tries BeautifulSoup first, falls back to regex.
    """
    try:
        from bs4 import BeautifulSoup  # noqa: F401
        return _parse_with_bs4(html)
    except ImportError:
        return _parse_with_regex(html)


def _parse_with_bs4(html: str) -> dict:
    """Parse reviews using BeautifulSoup."""
    from bs4 import BeautifulSoup

    soup = BeautifulSoup(html, "html.parser")

    # Business metadata
    name_el = soup.select_one(SELECTORS["business_name"])
    business_name = name_el.get_text(strip=True) if name_el else None

    address_el = soup.select_one(SELECTORS["business_address"])
    business_address = address_el.get_text(strip=True) if address_el else None

    category_el = soup.select_one(SELECTORS["business_category"])
    business_category = category_el.get_text(strip=True) if category_el else None

    rating_el = soup.select_one(SELECTORS["business_rating"])
    google_rating = None
    if rating_el:
        try:
            google_rating = float(rating_el.get_text(strip=True).replace(",", "."))
        except (ValueError, TypeError):
            pass

    total_count_el = soup.select_one(SELECTORS["total_review_count"])
    total_review_count = None
    if total_count_el:
        label = total_count_el.get("aria-label", "")
        count_match = re.search(r"([\d,]+)", label)
        if count_match:
            total_review_count = int(count_match.group(1).replace(",", ""))

    # Individual reviews
    reviews = []
    for container in soup.select(SELECTORS["review_container"]):
        reviewer_name = None
        name_el = container.select_one(SELECTORS["reviewer_name"])
        if name_el:
            reviewer_name = name_el.get_text(strip=True)

        star_rating = None
        rating_el = container.select_one(SELECTORS["star_rating"])
        if rating_el:
            aria = rating_el.get("aria-label", "")
            m = re.search(r"(\d)", aria)
            if m:
                star_rating = int(m.group(1))

        review_text = ""
        text_el = container.select_one(SELECTORS["review_text"])
        if text_el:
            review_text = text_el.get_text(strip=True)

        review_date = None
        date_el = container.select_one(SELECTORS["review_date"])
        if date_el:
            review_date = date_el.get_text(strip=True)

        reviewer_total_reviews = 1
        count_el = container.select_one(SELECTORS["reviewer_reviews_count"])
        if count_el:
            count_text = count_el.get_text(strip=True)
            m = re.search(r"(\d+)", count_text)
            if m:
                reviewer_total_reviews = int(m.group(1))

        if star_rating is not None:
            reviews.append({
                "reviewer_name": reviewer_name,
                "star_rating": star_rating,
                "review_text": review_text,
                "review_date": review_date,
                "reviewer_total_reviews": reviewer_total_reviews,
                "photo_count": 0,
            })

    return {
        "business_name": business_name,
        "business_address": business_address,
        "business_category": business_category,
        "google_rating": google_rating,
        "total_review_count": total_review_count if total_review_count else len(reviews),
        "reviews": reviews,
    }


def _parse_with_regex(html: str) -> dict:
    """Fallback parser using regex on the rendered HTML.

    Less reliable than BeautifulSoup but works without extra dependencies.
    """
    # Extract business name
    name_match = re.search(r'<h1[^>]*class="[^"]*DUGVrf[^"]*"[^>]*>(.*?)</h1>', html)
    business_name = name_match.group(1).strip() if name_match else None

    # Extract reviews
    reviews = []
    review_blocks = re.findall(
        r'data-review-id="[^"]*"(.*?)(?=data-review-id|$)', html, re.DOTALL
    )

    for block in review_blocks:
        reviewer_name = None
        nm = re.search(r'class="[^"]*d4r55[^"]*"[^>]*>(.*?)</div>', block)
        if nm:
            reviewer_name = re.sub(r"<[^>]+>", "", nm.group(1)).strip()

        star_rating = None
        rm = re.search(r'aria-label="(\d)\s*star', block)
        if rm:
            star_rating = int(rm.group(1))

        review_text = ""
        tm = re.search(r'class="[^"]*wiI7pd[^"]*"[^>]*>(.*?)</span>', block, re.DOTALL)
        if tm:
            review_text = re.sub(r"<[^>]+>", "", tm.group(1)).strip()

        review_date = None
        dm = re.search(r'class="[^"]*rsqaWe[^"]*"[^>]*>(.*?)</span>', block)
        if dm:
            review_date = re.sub(r"<[^>]+>", "", dm.group(1)).strip()

        reviewer_total_reviews = 1
        cm = re.search(r"(\d+)\s*review", block)
        if cm:
            reviewer_total_reviews = int(cm.group(1))

        if star_rating is not None:
            reviews.append({
                "reviewer_name": reviewer_name,
                "star_rating": star_rating,
                "review_text": review_text,
                "review_date": review_date,
                "reviewer_total_reviews": reviewer_total_reviews,
                "photo_count": 0,
            })

    return {
        "business_name": business_name,
        "business_address": None,
        "business_category": None,
        "google_rating": None,
        "total_review_count": len(reviews),
        "reviews": reviews,
    }
