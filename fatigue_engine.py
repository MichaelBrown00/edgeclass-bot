"""
EDGECLASS AI
Fixture Congestion & Fatigue Engine
Version 1
"""

from datetime import datetime


def calculate_fatigue(team_matches):
    """
    Calculates fatigue score (0-100)

    100 = Fully rested
    0 = Extremely fatigued
    """

    if not team_matches:
        return 100

    latest_match = team_matches[0]

    match_date = datetime.fromisoformat(
        latest_match["utcDate"].replace("Z", "+00:00")
    )

    days_rest = (datetime.now(match_date.tzinfo) - match_date).days

    if days_rest >= 7:
        return 100

    elif days_rest >= 5:
        return 90

    elif days_rest >= 4:
        return 82

    elif days_rest >= 3:
        return 74

    elif days_rest >= 2:
        return 65

    elif days_rest >= 1:
        return 55

    else:
        return 45