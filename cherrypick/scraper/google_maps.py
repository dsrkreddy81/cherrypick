"""Google Maps review scraper using Playwright directly.

Scrapes reviews from a Google Maps business listing by:
1. Launching a stealth Chromium browser
2. Navigating to the URL (handles short URL redirects)
3. Clicking the Reviews tab
4. Scrolling the reviews panel to load reviews
5. Expanding truncated review text
6. Extracting data via JS evaluation

CSS selectors are in SELECTORS dict at the top for easy updating
when Google changes their DOM structure.
"""

import asyncio
import random
import re

from playwright.async_api import async_playwright
from playwright_stealth import Stealth


# ----- CSS selectors (update when Google changes DOM) -----
SELECTORS = {
    "reviews_tab": 'button[aria-label*="Reviews"]',
    "reviews_tab_alt": 'button[data-tab-index="1"]',
    "review_container": "div.jftiEf",
    "review_container_alt": "div[data-review-id]",
    "reviewer_name": "div.d4r55",
    "star_rating": "span.kvMYJc",
    "review_text": "span.wiI7pd",
    "review_date": "span.rsqaWe",
    "reviewer_reviews_count": "span.RfnDt",
    "more_button": "button.w8nwRe",
    "scrollable_panel": "div.m6QErb.DxyBCb",
    "scrollable_panel_alt": 'div.m6QErb[role="feed"]',
    "business_name": "h1",
    "business_address": 'button[data-item-id="address"]',
    "business_category": 'button[jsaction*="category"]',
    "business_rating": "div.F7nice span[aria-hidden]",
    "total_review_count": 'span[aria-label*="reviews"]',
}


async def scrape_reviews(url: str, max_reviews: int = 500) -> dict:
    """Scrape reviews from a Google Maps business listing.

    Args:
        url: Google Maps URL (full or short maps.app.goo.gl link).
        max_reviews: Maximum number of reviews to collect.

    Returns:
        Dict with business_name, business_address, business_category,
        google_rating, total_review_count, reviews (list of dicts).
    """
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=True,
            args=[
                "--disable-blink-features=AutomationControlled",
                "--no-sandbox",
                "--disable-dev-shm-usage",
            ],
        )
        context = await browser.new_context(
            viewport={"width": 1280, "height": 900},
            locale="en-US",
            timezone_id="America/New_York",
        )
        page = await context.new_page()
        stealth = Stealth()
        await stealth.apply_stealth_async(page)

        try:
            # Step 1: Navigate (handles short URL redirects automatically)
            await page.goto(url, wait_until="domcontentloaded", timeout=60000)
            # Wait for the page to actually render something
            await page.wait_for_selector("h1", timeout=30000)
            await asyncio.sleep(2)

            # Step 2: Accept cookies if prompted
            try:
                accept_btn = page.locator('button:has-text("Accept all")')
                if await accept_btn.count() > 0:
                    await accept_btn.first.click()
                    await asyncio.sleep(1)
            except Exception:
                pass

            # Step 3: Click the Reviews tab
            clicked = False
            for selector in [SELECTORS["reviews_tab"], SELECTORS["reviews_tab_alt"]]:
                try:
                    tab = page.locator(selector)
                    if await tab.count() > 0:
                        await tab.first.click()
                        clicked = True
                        await asyncio.sleep(3)
                        break
                except Exception:
                    continue

            if not clicked:
                # Try clicking anything that says "reviews" in text
                try:
                    tab = page.locator('button:has-text("Reviews")')
                    if await tab.count() > 0:
                        await tab.first.click()
                        await asyncio.sleep(3)
                except Exception:
                    pass

            # Step 4: Find the scrollable reviews panel and scroll
            scrollable = None
            for sel in [SELECTORS["scrollable_panel"], SELECTORS["scrollable_panel_alt"]]:
                loc = page.locator(sel)
                if await loc.count() > 0:
                    scrollable = loc.first
                    break

            if scrollable:
                last_count = 0
                same_count_streak = 0

                for _ in range(200):
                    # Expand truncated reviews
                    more_buttons = page.locator(SELECTORS["more_button"])
                    count = await more_buttons.count()
                    for i in range(count):
                        try:
                            await more_buttons.nth(i).click(timeout=500)
                        except Exception:
                            pass

                    # Scroll down
                    await scrollable.evaluate("el => el.scrollTop = el.scrollHeight")
                    await asyncio.sleep(1.5 + random.random() * 2)

                    # Count reviews loaded
                    review_count = 0
                    for sel in [SELECTORS["review_container"], SELECTORS["review_container_alt"]]:
                        c = await page.locator(sel).count()
                        if c > review_count:
                            review_count = c

                    if max_reviews > 0 and review_count >= max_reviews:
                        break
                    if review_count == last_count:
                        same_count_streak += 1
                        if same_count_streak >= 3:
                            break
                    else:
                        same_count_streak = 0
                    last_count = review_count

                # Final expand of truncated text
                more_buttons = page.locator(SELECTORS["more_button"])
                for i in range(await more_buttons.count()):
                    try:
                        await more_buttons.nth(i).click(timeout=500)
                    except Exception:
                        pass
                await asyncio.sleep(1)

            # Step 5: Extract all data via JS
            data = await page.evaluate(_extraction_js())

            return data

        finally:
            await browser.close()


def _extraction_js() -> str:
    """Return JS that extracts business info + reviews from the loaded page."""
    return """() => {
        const data = {
            business_name: null,
            business_address: null,
            business_category: null,
            google_rating: null,
            total_review_count: 0,
            reviews: [],
        };

        // Business metadata
        const h1 = document.querySelector('h1');
        if (h1) data.business_name = h1.textContent.trim();

        const addrBtn = document.querySelector('button[data-item-id="address"]');
        if (addrBtn) data.business_address = addrBtn.textContent.trim();

        const catBtn = document.querySelector('button[jsaction*="category"]');
        if (catBtn) data.business_category = catBtn.textContent.trim();

        const ratingEl = document.querySelector('div.F7nice span[aria-hidden]');
        if (ratingEl) {
            const val = parseFloat(ratingEl.textContent.replace(',', '.'));
            if (!isNaN(val)) data.google_rating = val;
        }

        const countEl = document.querySelector('span[aria-label*="reviews"]');
        if (countEl) {
            const m = countEl.getAttribute('aria-label')?.match(/([\\d,]+)/);
            if (m) data.total_review_count = parseInt(m[1].replace(/,/g, ''));
        }

        // Reviews — try multiple container selectors
        const containers = document.querySelectorAll('div.jftiEf')?.length
            ? document.querySelectorAll('div.jftiEf')
            : document.querySelectorAll('div[data-review-id]');

        containers.forEach(el => {
            const nameEl = el.querySelector('div.d4r55');
            const ratingEl = el.querySelector('span.kvMYJc')
                || el.querySelector('span[role="img"]');
            const textEl = el.querySelector('span.wiI7pd');
            const dateEl = el.querySelector('span.rsqaWe');
            const countEl = el.querySelector('span.RfnDt');

            let starRating = null;
            if (ratingEl) {
                const aria = ratingEl.getAttribute('aria-label') || '';
                const m = aria.match(/(\\d)/);
                if (m) starRating = parseInt(m[1]);
            }

            let reviewerCount = 1;
            if (countEl) {
                const m = countEl.textContent.match(/(\\d+)/);
                if (m) reviewerCount = parseInt(m[1]);
            }

            if (starRating !== null) {
                data.reviews.push({
                    reviewer_name: nameEl ? nameEl.textContent.trim() : null,
                    star_rating: starRating,
                    review_text: textEl ? textEl.textContent.trim() : '',
                    review_date: dateEl ? dateEl.textContent.trim() : null,
                    reviewer_total_reviews: reviewerCount,
                    photo_count: 0,
                });
            }
        });

        if (!data.total_review_count) data.total_review_count = data.reviews.length;

        return data;
    }"""
