import datetime
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
    Fetch recent matches for one team.
    """

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

        data = response.json()

        return data.get("matches", [])

    except Exception as e:

        print(f"Error fetching team {team_id}:", e)

        return []
    

def analyze_match(match):

    home_id = match["homeTeam"]["id"]
    away_id = match["awayTeam"]["id"]

    home_matches = fetch_team_recent_matches(home_id)
    away_matches = fetch_team_recent_matches(away_id)

    def calculate_strength(team_id, matches):

        points = 0
        goals_scored = 0
        goals_conceded = 0

        for m in matches:

            home = m["homeTeam"]["id"] == team_id

            home_goals = m["score"]["fullTime"]["home"] or 0
            away_goals = m["score"]["fullTime"]["away"] or 0

            if home:

                goals_scored += home_goals
                goals_conceded += away_goals

                if home_goals > away_goals:
                    points += 3
                elif home_goals == away_goals:
                    points += 1

            else:

                goals_scored += away_goals
                goals_conceded += home_goals

                if away_goals > home_goals:
                    points += 3
                elif away_goals == home_goals:
                    points += 1

        strength = (
            points * 10
            + goals_scored * 2
            - goals_conceded
        )

        return strength

    home_strength = calculate_strength(home_id, home_matches)
    away_strength = calculate_strength(away_id, away_matches)

    difference = home_strength - away_strength

    if difference >= 12:
        return "Home Win", 88, 1.65

    elif difference <= -12:
        return "Away Win", 88, 1.70

    elif abs(difference) <= 4:
        return "BTTS", 78, 1.80

    else:
        return "Over 1.5 Goals", 82, 1.45
    

def analyze_match_premium(match):

    home_id = match["homeTeam"]["id"]
    away_id = match["awayTeam"]["id"]

    home_matches = fetch_team_recent_matches(home_id)
    away_matches = fetch_team_recent_matches(away_id)

    def stats(team_id, matches):

        wins = 0
        goals_for = 0
        goals_against = 0
        clean_sheets = 0
        btts = 0

        for m in matches:

            home = m["homeTeam"]["id"] == team_id

            hg = m["score"]["fullTime"]["home"] or 0
            ag = m["score"]["fullTime"]["away"] or 0

            if home:

                gf = hg
                ga = ag

            else:

                gf = ag
                ga = hg

            goals_for += gf
            goals_against += ga

            if gf > ga:
                wins += 1

            if ga == 0:
                clean_sheets += 1

            if gf > 0 and ga > 0:
                btts += 1

        games = max(len(matches), 1)

        return {

            "wins": wins,

            "gf_avg": goals_for / games,

            "ga_avg": goals_against / games,

            "clean": clean_sheets,

            "btts": btts

        }

    home = stats(home_id, home_matches)
    away = stats(away_id, away_matches)

    home_score = 0
    away_score = 0

    # Recent wins
    home_score += home["wins"] * 4
    away_score += away["wins"] * 4

    # Attack strength
    home_score += home["gf_avg"] * 6
    away_score += away["gf_avg"] * 6

    # Defensive strength
    home_score -= home["ga_avg"] * 4
    away_score -= away["ga_avg"] * 4

    # Clean sheets
    home_score += home["clean"] * 2
    away_score += away["clean"] * 2

    # Home advantage
    home_score += 5

    difference = home_score - away_score

    if difference >= 10:

        confidence = min(96, int(82 + abs(difference) / 3))
        return "Home Win", confidence, 1.65

    elif difference <= -10:

        confidence = min(96, int(82 + abs(difference) / 3))
        return "Away Win", confidence, 1.75

    elif home["btts"] >= 3 and away["btts"] >= 3:

        return "BTTS", 84, 1.90

    elif (home["gf_avg"] + away["gf_avg"]) >= 2.8:

        return "Over 2.5 Goals", 86, 1.95

    else:

        return "Over 1.5 Goals", 80, 1.45


def analyze_match_vip(match):

    return analyze_match_premium(match)


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

        fixture_id = match["id"]

        home = match["homeTeam"]["name"]
        away = match["awayTeam"]["name"]

        league = match["competition"]["name"]

        utc_time = datetime.fromisoformat(
        match["utcDate"].replace("Z", "+00:00")
        )

        local_time = utc_time + timedelta(hours=1)

        kickoff = local_time.strftime("%d %b • %H:%M")

        fixture_date = local_time.strftime("%A, %d %b")

        if plan == "vip":
            prediction, confidence, odds = analyze_match_vip(match)

        elif plan == "premium":
            prediction, confidence, odds = analyze_match_premium(match)

        else:
            prediction, confidence, odds = analyze_match(match)

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

            "actual_score": None
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

                fixture_id = match["id"]

                home = match["homeTeam"]["name"]
                away = match["awayTeam"]["name"]

                league = match["competition"]["name"]

                utc_time = datetime.fromisoformat(
                   match["utcDate"].replace("Z", "+00:00")
                )

                local_time = utc_time + timedelta(hours=1)

                kickoff = local_time.strftime("%d %b • %H:%M")

                fixture_date = local_time.strftime("%A, %d %b")

                if plan == "vip":
                    prediction, confidence, odds = analyze_match_vip(match)

                elif plan == "premium":
                    prediction, confidence, odds = analyze_match_premium(match)

                else:
                    prediction, confidence, odds = analyze_match(match)

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
                        "actual_score": None

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

    check_results()      