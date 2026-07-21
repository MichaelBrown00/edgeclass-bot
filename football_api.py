import datetime
import random
import requests

from database import (get_pending_predictions,update_prediction_result)

from config import FOOTBALL_API_KEY


def ai_model():
    print("========== NEW AI MODEL RUNNING ==========")
    """
    Fetch today's fixtures and generate AI predictions.
    """

    try:

        today = datetime.date.today().isoformat()

        print("TODAY:", today)

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
        )

        print("STATUS:", response.status_code)

        response = response.json()

        print(response)

        fixtures = response.get("response", [])

        print("Fixtures returned:", len(fixtures))

        if not fixtures:
            return []

    except Exception as e:

        print("Football API Error:", e)

        return []
    
    
def check_results():
    """
    Check every pending prediction and update it
    once the fixture has finished.
    """

    print("🔄 Scheduler running...")

    pending = get_pending_predictions()

    if not pending:
        print("No pending predictions.")
        return

    headers = {
        "x-apisports-key": FOOTBALL_API_KEY
    }

    for prediction in pending:

        prediction_id = prediction[0]
        fixture_id = prediction[1]
        saved_match = prediction[2]
        saved_bet = prediction[3]

        try:

            url = (
                f"https://v3.football.api-sports.io/"
                f"fixtures?id={fixture_id}"
            )

            response = requests.get(
                url,
                headers=headers,
                timeout=20
            ).json()

            fixtures = response.get("response", [])

            if not fixtures:
                print(f"No fixture found: {fixture_id}")
                continue

            fixture = fixtures[0]

            status = fixture["fixture"]["status"]["short"]

            if status != "FT":
                print(f"{saved_match} still not finished.")
                continue

            home_goals = fixture["goals"]["home"]
            away_goals = fixture["goals"]["away"]

            final_score = (
                f"{home_goals}-{away_goals}"
            )

            result = "LOSS"

            if (
                saved_bet == "Home Win"
                and home_goals > away_goals
            ):
                result = "WIN"

            elif (
                saved_bet == "Away Win"
                and away_goals > home_goals
            ):
                result = "WIN"

            elif (
                saved_bet == "Over 1.5 Goals"
                and (home_goals + away_goals) >= 2
            ):
                result = "WIN"

            elif (
                saved_bet == "Over 2.5 Goals"
                and (home_goals + away_goals) >= 3
            ):
                result = "WIN"

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
                f"✅ {saved_match} -> {result}"
            )

        except Exception as e:

            print(
                f"Error checking {saved_match}:",
                e
            )