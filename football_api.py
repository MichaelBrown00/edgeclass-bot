import datetime
import random
import requests

from database import (get_pending_predictions,update_prediction_result)

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

        print("TOTAL FIXTURES:", len(fixtures))

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

            print("RAW KICKOFF:", kickoff)

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
    
def check_results():
    """
    Checks finished matches and updates prediction results.
    """

    pending = get_pending_predictions()

    if not pending:
        print("No pending predictions.")
        return

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

        for prediction in pending:

            prediction_id = prediction[0]
            saved_match = prediction[1]
            saved_bet = prediction[2]

            for fixture in fixtures:

                home = fixture["teams"]["home"]["name"]
                away = fixture["teams"]["away"]["name"]

                match_name = f"{home} vs {away}"

                if match_name != saved_match:
                    continue

                status = fixture["fixture"]["status"]["short"]

                if status != "FT":
                    continue

                home_goals = fixture["goals"]["home"]
                away_goals = fixture["goals"]["away"]

                final_score = (
                    f"{home_goals}-{away_goals}"
                )

                result = "LOSS"

                # Home Win

                if (
                    saved_bet == "Home Win"
                    and home_goals > away_goals
                ):
                    result = "WIN"

                # Away Win

                elif (
                    saved_bet == "Away Win"
                    and away_goals > home_goals
                ):
                    result = "WIN"

                # Over 1.5

                elif (
                    saved_bet == "Over 1.5 Goals"
                    and (home_goals + away_goals) >= 2
                ):
                    result = "WIN"

                # Over 2.5

                elif (
                    saved_bet == "Over 2.5 Goals"
                    and (home_goals + away_goals) >= 3
                ):
                    result = "WIN"

                # BTTS

                elif (
                    saved_bet == "BTTS"
                    and home_goals > 0
                    and away_goals > 0
                ):
                    result = "WIN"

                update_prediction_result(
                    prediction_id,
                    result,
                    final_score
                )

                print(
                    f"{saved_match} -> {result}"
                )

    except Exception as e:

        print(
            "Result Checker Error:",
            e
        )