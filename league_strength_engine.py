LEAGUE_STRENGTH = {

    "UEFA Champions League": 100,

    "Premier League": 98,

    "La Liga": 96,

    "Serie A": 94,

    "Bundesliga": 93,

    "Ligue 1": 90,

    "Campeonato Brasileiro Série A": 88,

    "Major League Soccer": 82,

    "Eredivisie": 84,

    "Championship": 83

}


def get_league_strength(league_name):
    """
    Returns league quality.

    Unknown leagues default to 75.
    """

    return LEAGUE_STRENGTH.get(
        league_name,
        75
    )