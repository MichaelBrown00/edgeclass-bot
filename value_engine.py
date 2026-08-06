def calculate_value(model_probability, bookmaker_odds):
    """
    Calculates betting value.

    model_probability = AI probability (0-100)

    bookmaker_odds = decimal odds
    """

    implied_probability = 100 / bookmaker_odds

    edge = model_probability - implied_probability

    return round(edge, 2)


def classify_value(edge):

    if edge >= 15:
        return "🔥 ELITE VALUE"

    elif edge >= 10:
        return "💎 STRONG VALUE"

    elif edge >= 5:
        return "✅ GOOD VALUE"

    else:
        return "NO VALUE"