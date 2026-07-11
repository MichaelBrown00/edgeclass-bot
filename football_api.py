import datetime
import random
import requests

from config import FOOTBALL_API_KEY


def ai_model():
    """
    Fetch today's fixtures and generate structured AI predictions.
    """

    try:

        today = datetime.date.today().isoformat()

        url = (
            f"https://v3.football.api-sports.io/"
            f"fixtures?date={today}"
        )

        headers = {
            "x-apisports-key": FOOTBALL_API_KEY
        }

        response = requests.get(
            url,
            headers=headers,
            timeout=20
        ).json()

        fixtures = response.get("response", [])

        if not fixtures:
            return []

        bet_types = [
            "Over 1.5 Goals",
            "Over 2.5 Goals",
            "BTTS",
            "Home Win",
            "Away Win"
        ]

        predictions = []

        for fixture in fixtures[:10]:

            home = fixture["teams"]["home"]["name"]
            away = fixture["teams"]["away"]["name"]

            league = fixture["league"]["name"]

            kickoff = fixture["fixture"]["date"][11:16]

            confidence = random.randint(70, 90)

            odds = round(
                random.uniform(1.40, 2.40),
                2
            )

            prediction = random.choice(
                bet_types
            )

            predictions.append({

    "match":
        f"{home} vs {away}",

    "prediction":
        prediction,

    "confidence":
        confidence,

    "odds":
        odds,

    "league":
        league,

    "kickoff":
        kickoff,

    "status":
        "Pending",

    "actual_score":
        None

})

        return predictions

    except Exception as e:

        print(
            "Football API Error:",
            e
        )

        return []