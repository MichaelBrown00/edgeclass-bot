def initialize_market_scores():
    """
    Every betting market starts with zero points.
    """

    return {

        "Home Win": 0,

        "Away Win": 0,

        "Draw": 0,

        "Double Chance": 0,

        "BTTS": 0,

        "Over 1.5 Goals": 0,

        "Over 2.5 Goals": 0,

        "Under 2.5 Goals": 0

    }


def add_score(scores, market, points):
    """
    Adds points to a betting market.
    """

    if market in scores:
        scores[market] += points


def choose_best_market(scores):
    """
    Returns the betting market with the highest score.
    """

    winner = max(scores, key=scores.get)

    return winner


def calculate_market_confidence(scores):
    """
    Confidence based on how dominant the winning market is.
    """

    total_points = sum(scores.values())

    if total_points == 0:
        return 50

    winner = max(scores, key=scores.get)

    confidence = (scores[winner] / total_points) * 100

    confidence = max(55, min(98, confidence))

    return round(confidence)