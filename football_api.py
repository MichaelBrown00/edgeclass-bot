import datetime
import random
import requests

from datetime import datetime, timedelta

from database import (
    get_pending_predictions,
    update_prediction_result
)

import config


def fetch_today_fixtures():

    url = "https://api.football-data.org/v4/matches"

    headers = {
        "X-Auth-Token": config.FOOTBALL_DATA_KEY
    }

    try:

        response = requests.get(
            url,
            headers=headers,
            timeout=20
        )

        print("STATUS:", response.status_code)

        data = response.json()

        print("FULL RESPONSE:")
        print(data)

        matches = data.get("matches", [])

        print(f"Matches found: {len(matches)}")

        return matches

    except Exception as e:

        print("Football Data Error:", e)

        return []
    

def ai_model():
    """
    Generate today's predictions from Football-Data.org.
    """

    print("========== EDGECLASS AI ==========")
    print("TOKEN:", config.FOOTBALL_DATA_KEY[:8] + "...")

    matches = fetch_today_fixtures()

    if not matches:
        print("No fixtures found.")
        return []

    bet_types = [
        "Home Win",
        "Away Win",
        "Over 1.5 Goals",
        "Over 2.5 Goals",
        "BTTS"
    ]

    predictions = []

    for match in matches:

        fixture_id = match["id"]

        home = match["homeTeam"]["name"]
        away = match["awayTeam"]["name"]

        league = match["competition"]["name"]

        utc_time = datetime.fromisoformat(
        match["utcDate"].replace("Z", "+00:00")
        )

        local_time = utc_time + timedelta(hours=1)

        kickoff = local_time.strftime("%H:%M")

        prediction = random.choice(bet_types)

        confidence = random.randint(72, 90)

        odds = round(random.uniform(1.40, 2.30), 2)

        predictions.append({

            "fixture_id": fixture_id,

            "match": f"{home} vs {away}",

            "prediction": prediction,

            "confidence": confidence,

            "odds": odds,

            "league": league,

            "kickoff": kickoff,

            "status": "Pending",

            "actual_score": None
        })

    print(f"Generated {len(predictions)} predictions.")

    return predictions
    
    
def check_results():

    print("🔄 Scheduler running...")

    pending = get_pending_predictions()

    if not pending:
        print("No pending predictions.")
        return

    for prediction in pending:

        prediction_id = prediction[0]
        fixture_id = prediction[1]
        saved_match = prediction[2]
        saved_bet = prediction[3]

        try:

            url = f"https://api.football-data.org/v4/matches/{fixture_id}"

            response = requests.get(
            url,
            headers={
            "X-Auth-Token": config.FOOTBALL_DATA_KEY
            },
            timeout=20
            )

            response.raise_for_status()

            fixture = response.json()

            status = fixture["status"]

            if status != "FINISHED":
                print(f"{saved_match} still not finished.")
                continue

            home_goals = fixture["score"]["fullTime"]["home"]
            away_goals = fixture["score"]["fullTime"]["away"]

            final_score = f"{home_goals}-{away_goals}"

            result = "LOSS"

            if saved_bet == "Home Win" and home_goals > away_goals:
                result = "WIN"

            elif saved_bet == "Away Win" and away_goals > home_goals:
                result = "WIN"

            elif saved_bet == "Over 1.5 Goals" and (home_goals + away_goals) >= 2:
                result = "WIN"

            elif saved_bet == "Over 2.5 Goals" and (home_goals + away_goals) >= 3:
                result = "WIN"

            elif saved_bet == "BTTS" and home_goals > 0 and away_goals > 0:
                result = "WIN"

            update_prediction_result(
                prediction_id,
                result,
                final_score
            )

            print(f"✅ {saved_match} -> {result}")

        except Exception as e:

            print(f"Error checking {saved_match}: {e}")


if __name__ == "__main__":

    predictions = ai_model()

    for prediction in predictions:
        print(prediction)