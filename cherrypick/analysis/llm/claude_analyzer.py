import json
import os

from anthropic import Anthropic

_client = None

SYSTEM_PROMPT = """You are a fake review detection expert. You will be given a batch of reviews for a business. For each review, assess the probability that it is fake.

Consider these signals:
- Does the review contain specific, verifiable details (menu items, staff names, specific experiences)?
- Does the language feel natural or templated?
- Is the review consistent with the star rating?
- Does it read like AI-generated content?
- Is the level of enthusiasm proportional to the detail provided?

Return a JSON array. Each element must have:
- "review_id": the ID provided for that review
- "fake_probability": float 0.0 (definitely real) to 1.0 (definitely fake)
- "reasoning": one sentence explaining your assessment

Return ONLY the JSON array, no other text."""


def get_client() -> Anthropic:
    global _client
    if _client is None:
        _client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
    return _client


def build_prompt(business_name: str, business_category: str | None, reviews: list[dict]) -> str:
    lines = [f"Business: {business_name}"]
    if business_category:
        lines.append(f"Category: {business_category}")
    lines.append(f"\nAnalyze these {len(reviews)} reviews:\n")
    for r in reviews:
        lines.append(f"[Review ID: {r['id']}] Rating: {r['star_rating']}\u2605")
        lines.append(f"Text: {r['text']}")
        lines.append("")
    return "\n".join(lines)


def analyze_reviews_with_claude(
    business_name: str,
    business_category: str | None,
    reviews: list[dict],
    model: str = "claude-sonnet-4-20250514",
) -> list[dict]:
    if not reviews:
        return []
    client = get_client()
    prompt = build_prompt(business_name, business_category, reviews)
    response = client.messages.create(
        model=model,
        max_tokens=4096,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": prompt}],
    )
    response_text = response.content[0].text
    results = json.loads(response_text)
    return results
