from datetime import datetime
import re


def _parse_relative_date(date_str: str) -> datetime | None:
    if not date_str:
        return None

    try:
        return datetime.fromisoformat(date_str)
    except ValueError:
        pass

    now = datetime.utcnow()
    date_str = date_str.lower().strip()

    patterns = [
        (
            r"(\d+)\s*day",
            lambda m: now.replace(day=max(1, now.day - int(m.group(1)))),
        ),
        (
            r"(\d+)\s*week",
            lambda m: datetime(
                now.year, now.month, max(1, now.day - int(m.group(1)) * 7)
            ),
        ),
        (
            r"(\d+)\s*month",
            lambda m: datetime(
                now.year, max(1, now.month - int(m.group(1))), now.day
            ),
        ),
        (
            r"a\s*month",
            lambda m: datetime(now.year, max(1, now.month - 1), now.day),
        ),
        (
            r"(\d+)\s*year",
            lambda m: datetime(now.year - int(m.group(1)), now.month, now.day),
        ),
        (
            r"a\s*year",
            lambda m: datetime(now.year - 1, now.month, now.day),
        ),
    ]

    for pattern, factory in patterns:
        match = re.search(pattern, date_str)
        if match:
            try:
                return factory(match)
            except ValueError:
                return now

    return None


def score_timing_clusters(dates: list[str], window_days: int = 3) -> list[float]:
    if not dates:
        return []

    parsed = [_parse_relative_date(d) for d in dates]
    n = len(parsed)

    if n < 3:
        return [0.0] * n

    scores = []
    for i, dt in enumerate(parsed):
        if dt is None:
            scores.append(0.0)
            continue

        nearby = 0
        for j, other_dt in enumerate(parsed):
            if i == j or other_dt is None:
                continue
            diff = abs((dt - other_dt).days)
            if diff <= window_days:
                nearby += 1

        ratio = nearby / n
        score = min(1.0, ratio / 0.3)
        scores.append(round(score, 3))

    return scores
