import requests
import time

from datetime import datetime, timedelta

from prediction_engine import predict_match

from database import (
    get_pending_predictions,
    update_prediction_result
)

import config

# ============================================
# TEAM FORM CACHE
# ============================================

TEAM_FORM_CACHE = {}


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
    

def fetch_fixtures_for_date(date_string):

    url = (
        "https://api.football-data.org/v4/matches"
        f"?dateFrom={date_string}&dateTo={date_string}"
    )

    headers = {
        "X-Auth-Token": config.FOOTBALL_DATA_KEY
    }

    try:

        response = requests.get(
            url,
            headers=headers,
            timeout=20
        )

        response.raise_for_status()

        data = response.json()

        matches = data.get("matches", [])

        print(f"{date_string}: {len(matches)} matches")

        return matches

    except Exception as e:

        print(e)

        return []
    

def fetch_team_recent_matches(team_id, limit=5):
    """
    Fetch recent matches with memory cache.
    """

    if team_id in TEAM_FORM_CACHE:
        return TEAM_FORM_CACHE[team_id]

    url = (
        f"https://api.football-data.org/v4/"
        f"teams/{team_id}/matches?limit={limit}"
    )

    headers = {
        "X-Auth-Token": config.FOOTBALL_DATA_KEY
    }

    try:

        response = requests.get(
            url,
            headers=headers,
            timeout=20
        )

        response.raise_for_status()

        matches = response.json().get("matches", [])

        TEAM_FORM_CACHE[team_id] = matches

        return matches

    except Exception as e:

        print(f"Error fetching team {team_id}: {e}")

        return []
    

def ai_model(plan="premium"):
    """
    Generate today's predictions from Football-Data.org.
    """

    print("========== EDGECLASS AI ==========")
    print("TOKEN:", config.FOOTBALL_DATA_KEY[:8] + "...")

    matches = fetch_today_fixtures()

    # No fixtures today? Search ahead depending on plan.
    if not matches:
 
        if plan == "vip":
            search_days = 7

        elif plan == "premium":
            search_days = 4

        else:
            search_days = 0

        for i in range(1, search_days + 1):

            future_date = (
                datetime.now() + timedelta(days=i)
            ).strftime("%Y-%m-%d")

            print(f"Searching {future_date}...")

            matches = fetch_fixtures_for_date(future_date)

            if matches:

                print(f"Found fixtures on {future_date}")

                break

        if not matches:

            print("No fixtures found.")

            return []

    predictions = []

    for match in matches:

        if match["status"] != "SCHEDULED":
            continue

        fixture_id = match["id"]

        home = match["homeTeam"]["name"]
        away = match["awayTeam"]["name"]

        home_id = match["homeTeam"]["id"]
        away_id = match["awayTeam"]["id"]

        home_matches = fetch_team_recent_matches(home_id)
        away_matches = fetch_team_recent_matches(away_id)

        league = match["competition"]["name"]

        utc_time = datetime.fromisoformat(
        match["utcDate"].replace("Z", "+00:00")
        )

        local_time = utc_time + timedelta(hours=1)

        kickoff = local_time.strftime("%d %b • %H:%M")

        fixture_date = local_time.strftime("%A, %d %b")

        result = predict_match(
            match,
            home_id,
            away_id,
            home_matches,
            away_matches
        )

        prediction = result["prediction"]
        confidence = result["confidence"]
        odds = result["odds"]

        home_rating = result["home_rating"]
        away_rating = result["away_rating"]

        grade = result["grade"]
        value = result["value"]
        edge = result["edge"]

        reasoning = "\n".join(result["reasoning"])

        # ===========================
        # ADVANCED AI METRICS
        # ===========================

        home_form = result["home_form"]
        away_form = result["away_form"]

        home_attack = result["home_attack"]
        away_attack = result["away_attack"]

        home_defense = result["home_defense"]
        away_defense = result["away_defense"]

        home_momentum = result["home_momentum"]
        away_momentum = result["away_momentum"]

        home_xg = result["home_xg"]
        away_xg = result["away_xg"]

        home_xga = result["home_xga"]
        away_xga = result["away_xga"]

        predictions.append({

            "fixture_id": fixture_id,

            "match": f"{home} vs {away}",

            "prediction": prediction,

            "confidence": confidence,

            "odds": odds,

            "league": league,

            "kickoff": kickoff,

            "fixture_date": fixture_date,

            "status": "Pending",

            "actual_score": None,

            "grade": grade,

            "value": value,

            "edge": edge,

            "reasoning": reasoning,

            "home_rating": home_rating,

            "away_rating": away_rating,

            "home_form": home_form,
            "away_form": away_form,

            "home_attack": home_attack,
            "away_attack": away_attack,

            "home_defense": home_defense,
            "away_defense": away_defense,

            "home_momentum": home_momentum,
            "away_momentum": away_momentum,

            "home_xg": home_xg,
            "away_xg": away_xg,

            "home_xga": home_xga,
            "away_xga": away_xga,
        })

    # Confidence threshold
    if plan == "vip":
        minimum_confidence = 90
        max_search_days = 7

    elif plan == "premium":
        minimum_confidence = 75
        max_search_days = 4

    else:
        minimum_confidence = 75
        max_search_days = 0


    predictions = [
        p for p in predictions
        if p["confidence"] >= minimum_confidence
    ]


    # Premium/VIP: if today's matches aren't good enough,
    # keep searching future days.
    if not predictions and max_search_days > 0:

        print("No strong edge today. Searching future fixtures...")

        for day in range(1, max_search_days + 1):

            future_date = (
                datetime.now() + timedelta(days=day)
            ).strftime("%Y-%m-%d")

            matches = fetch_fixtures_for_date(future_date)

            if not matches:
               continue

            predictions = []

            for match in matches:

                if match["status"] != "SCHEDULED":
                     continue

                fixture_id = match["id"]

                home = match["homeTeam"]["name"]
                away = match["awayTeam"]["name"]

                home_id = match["homeTeam"]["id"]
                away_id = match["awayTeam"]["id"]

                home_matches = fetch_team_recent_matches(home_id)
                away_matches = fetch_team_recent_matches(away_id)

                league = match["competition"]["name"]

                utc_time = datetime.fromisoformat(
                   match["utcDate"].replace("Z", "+00:00")
                )

                local_time = utc_time + timedelta(hours=1)

                kickoff = local_time.strftime("%d %b • %H:%M")

                fixture_date = local_time.strftime("%A, %d %b")

                result = predict_match(
                    match,
                    home_id,
                    away_id,
                    home_matches,
                    away_matches
                )

                prediction = result["prediction"]
                confidence = result["confidence"]
                odds = result["odds"]

                home_rating = result["home_rating"]
                away_rating = result["away_rating"]

                grade = result["grade"]
                value = result["value"]
                edge = result["edge"]

                reasoning = "\n".join(result["reasoning"])

                # ===========================
                # ADVANCED AI METRICS
                # ===========================

                home_form = result["home_form"]
                away_form = result["away_form"]

                home_attack = result["home_attack"]
                away_attack = result["away_attack"]

                home_defense = result["home_defense"]
                away_defense = result["away_defense"]

                home_momentum = result["home_momentum"]
                away_momentum = result["away_momentum"]

                home_xg = result["home_xg"]
                away_xg = result["away_xg"]

                home_xga = result["home_xga"]
                away_xga = result["away_xga"]

                if confidence >= minimum_confidence:

                    predictions.append({

                        "fixture_id": fixture_id,
                        "match": f"{home} vs {away}",
                        "prediction": prediction,
                        "confidence": confidence,
                        "odds": odds,
                        "league": league,
                        "kickoff": kickoff,
                        "fixture_date": fixture_date,
                        "status": "Pending",
                        "actual_score": None,

                        "grade": grade,
                        "value": value,
                        "edge": edge,
                        "reasoning": reasoning,
                        "home_rating": home_rating,
                        "away_rating": away_rating,

                        "home_form": home_form,
                        "away_form": away_form,

                        "home_attack": home_attack,
                        "away_attack": away_attack,

                        "home_defense": home_defense,
                        "away_defense": away_defense,

                        "home_momentum": home_momentum,
                        "away_momentum": away_momentum,

                        "home_xg": home_xg,
                        "away_xg": away_xg,

                        "home_xga": home_xga,
                        "away_xga": away_xga,

                   })

            if predictions:

                print(f"Found {len(predictions)} strong predictions on {future_date}")
                break

    print(f"Generated {len(predictions)} predictions.")

    return predictions
    
    
def update_finished_predictions():

    headers = {
    "X-Auth-Token": config.FOOTBALL_DATA_KEY
    }

    pending = get_pending_predictions()

    print(f"Pending predictions: {len(pending)}")

    for row in pending:

        prediction_id = row[0]
        fixture_id = row[1]
        match_name = row[2]
        prediction = row[3]

        print(f"Checking fixture {fixture_id}")

        response = requests.get(
            f"https://api.football-data.org/v4/matches/{fixture_id}",
            headers=headers
        )

        if response.status_code != 200:
            print("Could not retrieve match.")
            continue

        match = response.json()

        if match["status"] != "FINISHED":
            print("Match not finished yet.")
            continue

        print("Finished match found.")


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

        if fixture_id is None:
            print(f"Skipping prediction {prediction_id}: no fixture_id")
            continue

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

            if status == "POSTPONED":
                print(f"⏸ {saved_match} has been postponed.")
                continue

            if status in ["SCHEDULED", "TIMED", "IN_PLAY", "PAUSED"]:
                print(f"⏳ {saved_match} still not finished.")
                continue

            if status != "FINISHED":
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

        except requests.exceptions.HTTPError as e:

            if e.response is not None and e.response.status_code == 429:

               print("⚠ Rate limit reached. Waiting 60 seconds...")

               time.sleep(60)

               continue

            print(f"Error checking {saved_match}: {e}")

        except Exception as e:

            print(f"Error checking {saved_match}: {e}")

        time.sleep(1)   


if __name__ == "__main__":
    predictions = ai_model()

    for prediction in predictions:
        print(prediction)

    check_results()  


from datetime import datetime, timedelta


def get_finished_matches():
    """
    Returns all finished matches from the last 7 days.
    Compatible with Football-Data.org.
    """

    today = datetime.utcnow().date()

    all_matches = []

    for i in range(7):

        day = today - timedelta(days=i)

        matches = fetch_fixtures_for_date(day.isoformat())

        for match in matches:

            if match["status"] == "FINISHED":

                all_matches.append({

                    "fixture_id": match["id"],

                    "home_team": match["homeTeam"]["name"],

                    "away_team": match["awayTeam"]["name"],

                    "home_goals": match["score"]["fullTime"]["home"],

                    "away_goals": match["score"]["fullTime"]["away"],

                    "winner": match["score"]["winner"]

                })

    return all_matches  


def get_fixture_by_id(fixture_id):
    """
    Fetch one fixture directly from Football-Data.org.
    """

    url = f"https://api.football-data.org/v4/matches/{fixture_id}"

    headers = {
        "X-Auth-Token": config.FOOTBALL_DATA_KEY
    }

    try:

        response = requests.get(
            url,
            headers=headers,
            timeout=20
        )

        response.raise_for_status()

        data = response.json()

        print("\n====================")
        print(f"Fixture ID: {fixture_id}")
        print(data)
        print("====================\n")

        return data

    except Exception as e:

        print(f"Fixture {fixture_id} error:", e)

        return None