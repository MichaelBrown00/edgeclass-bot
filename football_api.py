import datetime
import random
import requests

from config import FOOTBALL_API_KEY


def ai_model():
    """
    Fetch today's fixtures and generate prediction candidates.
    """

    try:
        today = datetime.date.today().isoformat()

        url = f"https://v3.football.api-sports.io/fixtures?date={today}"

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

            confidence = random.randint(70, 90)

            bet = random.choice(bet_types)

            predictions.append(
                f"{home} vs {away}\n"
                f"Bet: {bet}\n"
                f"Confidence: {confidence}%"
            )

        return predictions

    except Exception as e:
        print("Football API Error:", e)
        return []