def calculate_home_away_strength(team_id, matches, home=True):
    """
    Calculates how strong a team is when playing
    at home or away.
    """

    games = 0
    wins = 0
    goals_for = 0
    goals_against = 0

    for match in matches:

        is_home = match["homeTeam"]["id"] == team_id

        if is_home != home:
            continue

        games += 1

        hg = match["score"]["fullTime"]["home"] or 0
        ag = match["score"]["fullTime"]["away"] or 0

        if is_home:
            gf = hg
            ga = ag
        else:
            gf = ag
            ga = hg

        goals_for += gf
        goals_against += ga

        if gf > ga:
            wins += 1

    if games == 0:
        return 50

    win_rate = wins / games

    attack = goals_for / games
    defense = goals_against / games

    score = (
        win_rate * 60 +
        attack * 25 -
        defense * 15
    )

    return round(max(0, min(score, 100)), 2)