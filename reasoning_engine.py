def generate_reasoning(
    prediction,
    home_form,
    away_form,
    home_attack,
    away_attack,
    home_defense,
    away_defense,
    home_xg,
    away_xg,
    h2h,
    squad
):

    reasons = []

    if home_form > away_form:
        reasons.append("Home team has better recent form.")

    elif away_form > home_form:
        reasons.append("Away team has stronger recent form.")

    if home_attack > away_attack:
        reasons.append("Home attack is creating more chances.")

    elif away_attack > home_attack:
        reasons.append("Away attack has been more dangerous.")

    if home_defense > away_defense:
        reasons.append("Home defense has been more solid.")

    elif away_defense > home_defense:
        reasons.append("Away defense is stronger.")

    if home_xg["xg"] > away_xg["xg"]:
        reasons.append("Expected goals favour the home side.")

    elif away_xg["xg"] > home_xg["xg"]:
        reasons.append("Expected goals favour the away side.")

    if h2h["home_wins"] > h2h["away_wins"]:
        reasons.append("Historical meetings favour the home team.")

    elif h2h["away_wins"] > h2h["home_wins"]:
        reasons.append("Historical meetings favour the away team.")

    if squad["home"] > squad["away"]:
        reasons.append("Home squad quality is higher.")

    elif squad["away"] > squad["home"]:
        reasons.append("Away squad quality is higher.")

    return reasons