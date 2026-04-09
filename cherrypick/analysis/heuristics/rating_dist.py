from collections import Counter


def score_rating_distribution(ratings: list[int]) -> float:
    if len(ratings) < 5:
        return 0.0

    counts = Counter(ratings)
    total = len(ratings)
    dist = {i: counts.get(i, 0) / total for i in range(1, 6)}

    score = 0.0

    if dist[5] > 0.8:
        score += 0.5

    middle = dist[2] + dist[3] + dist[4]
    if middle < 0.1 and total > 10:
        score += 0.3

    if dist[5] > 0.6 and dist[1] > 0.05 and middle < 0.15:
        score += 0.3

    return min(1.0, round(score, 3))
