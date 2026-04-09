import math


def score_single_review_accounts(review_counts: list[int]) -> list[float]:
    scores = []
    for count in review_counts:
        if count <= 0:
            count = 1
        score = max(0.0, 1.0 - (math.log(count + 1) / math.log(50)))
        scores.append(round(score, 3))
    return scores
