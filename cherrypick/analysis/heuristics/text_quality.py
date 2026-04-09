import re

GENERIC_PHRASES = [
    "highly recommend", "great place", "amazing experience",
    "will definitely come back", "best in town", "loved it",
    "must visit", "five stars", "5 stars", "wonderful experience",
    "absolutely amazing", "top notch", "couldn't be happier",
    "exceeded expectations",
]


def score_text_quality(text: str) -> float:
    if not text or not text.strip():
        return 0.9
    text_lower = text.lower().strip()
    word_count = len(text_lower.split())
    score = 0.0
    if word_count < 5:
        score += 0.4
    elif word_count < 15:
        score += 0.2
    generic_count = sum(1 for phrase in GENERIC_PHRASES if phrase in text_lower)
    score += min(0.3, generic_count * 0.1)
    has_numbers = bool(re.search(r"\d", text))
    has_dollar = bool(re.search(r"\$\d", text))
    has_proper_nouns = bool(re.search(r"[A-Z][a-z]{2,}", text[1:])) if len(text) > 1 else False
    specificity_signals = sum([has_numbers, has_dollar, has_proper_nouns])
    if specificity_signals == 0:
        score += 0.2
    if text.isupper() and word_count > 3:
        score += 0.1
    exclamation_ratio = text.count("!") / max(1, word_count)
    if exclamation_ratio > 0.3:
        score += 0.1
    return min(1.0, round(score, 3))
