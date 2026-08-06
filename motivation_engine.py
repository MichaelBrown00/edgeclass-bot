def calculate_motivation(match):
    """
    Temporary motivation model.

    Later this will use:
    - League position
    - Relegation battles
    - Title race
    - European qualification
    - Cup finals
    - Derby matches

    For now it returns neutral motivation.
    """

    return {
        "home": 50,
        "away": 50
    }