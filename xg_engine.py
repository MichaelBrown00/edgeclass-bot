def calculate_expected_goals(team_id, matches):
    """
    Estimate attacking xG and defensive xGA
    using recent performances.
    """

    goals_for = 0
    goals_against = 0

    for match in matches:

        if match["homeTeam"]["id"] == team_id:
            gf = match["score"]["fullTime"]["home"] or 0
            ga = match["score"]["fullTime"]["away"] or 0
        else:
            gf = match["score"]["fullTime"]["away"] or 0
            ga = match["score"]["fullTime"]["home"] or 0

        goals_for += gf
        goals_against += ga

    games = max(len(matches), 1)

    xg = goals_for / games
    xga = goals_against / games

    return {
        "xg": round(xg, 2),
        "xga": round(xga, 2)
    }