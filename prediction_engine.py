"""
==========================================
EDGECLASS AI V2
Prediction Engine
==========================================
"""

from collections import Counter
from dynamic_weights import get_dynamic_weights
from unittest import signals

from injury_engine import calculate_squad_strength
from fatigue_engine import calculate_fatigue
from confidence_engine import calculate_confidence
from xg_engine import calculate_expected_goals
from referee_engine import calculate_referee
from home_away_engine import calculate_home_away_strength
from league_strength_engine import get_league_strength
from motivation_engine import calculate_motivation
from weather_engine import calculate_weather
from engine_tracker import get_accuracy
from grade_engine import calculate_prediction_grade
from value_engine import (
    calculate_value,
    classify_value
)

from reasoning_engine import generate_reasoning
from decision_engine import (
    initialize_market_scores,
    add_score,
    choose_best_market,
    calculate_market_confidence
)

SQUAD_BASELINE = 85


def calculate_form(team_id, matches):
    """
    Calculates recent form from the last matches.

    Returns a score between 0 and 100.
    """

    if not matches:
        return 50

    points = 0

    for match in matches:

        home = match["homeTeam"]["id"] == team_id

        home_goals = match["score"]["fullTime"]["home"] or 0
        away_goals = match["score"]["fullTime"]["away"] or 0

        if home:

            if home_goals > away_goals:
                points += 3

            elif home_goals == away_goals:
                points += 1

        else:

            if away_goals > home_goals:
                points += 3

            elif away_goals == home_goals:
                points += 1

    maximum_points = len(matches) * 3

    return round((points / maximum_points) * 100)


def calculate_recent_momentum(team_id, matches):
    """
    Measures recent momentum.

    Newer matches are worth more than older ones.

    Returns:
        Score between 0 and 100.
    """

    if not matches:
        return 50

    # Oldest → Newest weights
    weights = [1, 2, 3, 4, 5]

    # Keep only last 5 matches
    recent = matches[-5:]

    # Adjust weights if fewer than 5 games
    weights = weights[-len(recent):]

    total_points = 0
    max_points = 0

    for weight, match in zip(weights, recent):

        home = match["homeTeam"]["id"] == team_id

        hg = match["score"]["fullTime"]["home"] or 0
        ag = match["score"]["fullTime"]["away"] or 0

        if home:

            if hg > ag:
                points = 3
            elif hg == ag:
                points = 1
            else:
                points = 0

        else:

            if ag > hg:
                points = 3
            elif ag == hg:
                points = 1
            else:
                points = 0

        total_points += points * weight
        max_points += 3 * weight

    score = (total_points / max_points) * 100

    return round(score)


def fetch_head_to_head(home_id, away_id):
    """
    Fetch previous meetings between two teams.
    """

    url = (
        "https://api.football-data.org/v4/matches"
        f"?status=FINISHED"
        f"&limit=10"
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

        h2h = []

        for match in matches:

            ids = [
                match["homeTeam"]["id"],
                match["awayTeam"]["id"]
            ]

            if home_id in ids and away_id in ids:
                h2h.append(match)

        return h2h

    except Exception:

        return []


def analyze_head_to_head(home_id, away_id):
    """
    Analyze previous meetings between both clubs.

    Returns:
        {
            "home_wins": int,
            "away_wins": int,
            "draws": int,
            "btts": int,
            "over25": int
        }
    """

    matches = fetch_head_to_head(home_id, away_id)

    stats = {
        "home_wins": 0,
        "away_wins": 0,
        "draws": 0,
        "btts": 0,
        "over25": 0
    }

    for match in matches:

        home = match["homeTeam"]["id"]
        away = match["awayTeam"]["id"]

        hg = match["score"]["fullTime"]["home"] or 0
        ag = match["score"]["fullTime"]["away"] or 0

        # Convert result into perspective of today's home/away teams
        if home == home_id:

            if hg > ag:
                stats["home_wins"] += 1

            elif hg < ag:
                stats["away_wins"] += 1

            else:
                stats["draws"] += 1

        else:

            if hg > ag:
                stats["away_wins"] += 1

            elif hg < ag:
                stats["home_wins"] += 1

            else:
                stats["draws"] += 1

        # BTTS
        if hg > 0 and ag > 0:
            stats["btts"] += 1

        # Over 2.5
        if hg + ag >= 3:
            stats["over25"] += 1

    return stats


def calculate_attack(team_id, matches):
    """
    Measures how dangerous a team's attack is.

    Returns a score between 0 and 100.
    """

    if not matches:
        return 50

    goals_scored = 0

    for match in matches:

        home = match["homeTeam"]["id"] == team_id

        home_goals = match["score"]["fullTime"]["home"] or 0
        away_goals = match["score"]["fullTime"]["away"] or 0

        if home:
            goals_scored += home_goals
        else:
            goals_scored += away_goals

    average_goals = goals_scored / len(matches)

    score = min(average_goals * 40, 100)

    return round(score)


def calculate_defense(team_id, matches):
    """
    Measures defensive strength.

    Returns a score between 0 and 100.

    Higher score = better defense.
    """

    if not matches:
        return 50

    goals_conceded = 0

    for match in matches:

        home = match["homeTeam"]["id"] == team_id

        home_goals = match["score"]["fullTime"]["home"] or 0
        away_goals = match["score"]["fullTime"]["away"] or 0

        if home:
            goals_conceded += away_goals
        else:
            goals_conceded += home_goals

    average_conceded = goals_conceded / len(matches)

    score = 100 - (average_conceded * 40)

    score = max(0, min(score, 100))

    return round(score)


def calculate_team_rating(team_id, matches, home=False):
    """
    Combines every metric into one overall team rating.

    Returns:
        Integer score between 0 and 100
    """

    form = calculate_form(team_id, matches)

    attack = calculate_attack(team_id, matches)

    defense = calculate_defense(team_id, matches)

    # NEW
    momentum = calculate_recent_momentum(team_id, matches)

    home_bonus = 5 if home else 0

    rating = (
        form * 0.30 +
        momentum * 0.25 +
        attack * 0.25 +
        defense * 0.20
    )

    rating += home_bonus

    rating = min(rating, 100)

    return round(rating, 2)


def predict_match(
    match,    
    home_team_id,
    away_team_id,
    home_matches,
    away_matches
):
    """
    EdgeClass AI Match Predictor
    """

    scores = initialize_market_scores()

    weights = get_dynamic_weights()

    home_form = calculate_form(home_team_id, home_matches)
    away_form = calculate_form(away_team_id, away_matches)

    # FORM ENGINE VOTES

    if home_form > away_form:

        form_weight = weights("form")

        add_score(
            scores,
            "Home Win",
            12 * form_weight
        )

        add_score(scores, "Double Chance", 6)

    elif away_form > home_form:

        form_weight = weights["form"]

        add_score(
            scores,
            "Away Win",
            12 * form_weight
        )

        add_score(scores, "Double Chance", 6)

    else:

        add_score(scores, "Draw", 8)

    home_attack = calculate_attack(home_team_id, home_matches)
    away_attack = calculate_attack(away_team_id, away_matches)

    # ==============================
    # ATTACK ENGINE VOTES
    # ==============================

    if home_attack >= 80:

        attack_weight = weights["attack"]

        add_score(
           scores,
           "Home Win",
           10 * attack_weight
       )
        add_score(scores, "Over 2.5 Goals", 6)

    if away_attack >= 80:

        add_score(
            scores,
            "Away Win",
            10 * attack_weight
        )
        add_score(scores, "Over 2.5 Goals", 6)

    if home_attack >= 75 and away_attack >= 75:

        add_score(scores, "BTTS", 12)
        add_score(scores, "Over 2.5 Goals", 10)

    elif home_attack >= 70 or away_attack >= 70:

        add_score(scores, "Over 1.5 Goals", 8)

    home_defense = calculate_defense(home_team_id, home_matches)
    away_defense = calculate_defense(away_team_id, away_matches)

    # ==============================
    # DEFENSE ENGINE VOTES
    # ==============================

    # Strong defenses usually favor lower-scoring matches
    if home_defense >= 80 and away_defense >= 80:

        defense_weight = weights["defense"]

        add_score(
            scores,
           "Under 2.5 Goals",
           12 * defense_weight
        )
        add_score(scores, "Double Chance", 6)

    # Weak defenses usually favor goals
    elif home_defense <= 60 and away_defense <= 60:

        add_score(scores, "BTTS", 10)
        add_score(scores, "Over 2.5 Goals", 10)

    # One weak defense often still produces goals
    elif home_defense <= 60 or away_defense <= 60:

          add_score(scores, "Over 1.5 Goals", 8)

    home_momentum = calculate_recent_momentum(
        home_team_id,
        home_matches
    )

    away_momentum = calculate_recent_momentum(
        away_team_id,
        away_matches
    )      

    # ==============================
    # MOMENTUM ENGINE VOTES
    # ==============================

    if home_momentum >= 80:

        momentum_weight = weights["momentum"]

        add_score(
            scores,
            "Home Win",
            10 * momentum_weight
        )    

    elif away_momentum >= 80:

        add_score(
            scores,
            "Away Win",
            10 * momentum_weight
        )

    if abs(home_momentum - away_momentum) <= 5:

        add_score(scores, "Double Chance", 6)

    home_rating = calculate_team_rating(
        home_team_id,
        home_matches,
        home=True
    )

    away_rating = calculate_team_rating(
        away_team_id,
        away_matches,
        home=False
    )

    home_rating += (home_momentum - 75) * 0.20
    away_rating += (away_momentum - 75) * 0.20

    # Squad Strength (85 = neutral baseline)
    squad = calculate_squad_strength(
        home_team_id,
        away_team_id
    )

    home_rating += (squad["home"] - SQUAD_BASELINE) * 0.25
    away_rating += (squad["away"] - SQUAD_BASELINE) * 0.25

    # Fatigue Engine
    home_fatigue = calculate_fatigue(home_matches)
    away_fatigue = calculate_fatigue(away_matches)
    
    home_rating += (home_fatigue - 85) * 0.20
    away_rating += (away_fatigue - 85) * 0.20

    # Expected Goals (xG)
    home_xg = calculate_expected_goals(
    home_team_id,
    home_matches
    )

    away_xg = calculate_expected_goals(
    away_team_id,
    away_matches
    )

    # Better attacking xG increases rating
    home_rating += home_xg["xg"] * 3
    away_rating += away_xg["xg"] * 3

    # Lower xGA means stronger defense
    home_rating -= home_xg["xga"] * 2
    away_rating -= away_xg["xga"] * 2

    # ==============================
    # xG ENGINE VOTES
    # ==============================

    # Strong attacking expected goals
    if home_xg["xg"] >= 2.0:
        xg_weight = weights["xg"]

        add_score(
            scores,
            "Home Win",
            10 * xg_weight
        )
        add_score(scores, "Over 2.5 Goals", 8)

    if away_xg["xg"] >= 2.0:
        add_score(
            scores,
            "Away Win",
            10 * xg_weight
        )
        add_score(scores, "Over 2.5 Goals", 8)

    # Both teams creating lots of chances
    if  home_xg["xg"] >= 1.5 and away_xg["xg"] >= 1.5:
        add_score(scores, "BTTS", 12)

    # Weak defenses (high expected goals against)
    if home_xg["xga"] >= 1.6 or away_xg["xga"] >= 1.6:
        add_score(scores, "Over 2.5 Goals", 8)

    h2h = analyze_head_to_head(
        home_team_id,
        away_team_id
    )    

    # ==============================
    # H2H ENGINE VOTES
    # ==============================

    # Previous meetings favour today's home team
    if h2h["home_wins"] > h2h["away_wins"]:

        h2h_weight = weights["h2h"]

        add_score(
            scores,
            "Home Win",
            8 * h2h_weight
        )
        add_score(scores, "Double Chance", 5)

    # Previous meetings favour today's away team
    elif h2h["away_wins"] > h2h["home_wins"]:

        add_score(
            scores,
            "Away Win",
            8 * h2h_weight
        )
        add_score(scores, "Double Chance", 5)

    # Lots of draws between these teams
    if h2h["draws"] >= 2:

        add_score(scores, "Draw", 6)

    # BTTS history
    if h2h["btts"] >= 3:

       add_score(scores, "BTTS", 8)

    # Over 2.5 history
    if h2h["over25"] >= 3:

       add_score(scores, "Over 2.5 Goals", 8)

    """
# ==========================================
# OLD H2H ENGINE (Archived)
# ==========================================
# This was an older version that expected:
#   h2h["winner"]
#   h2h["btts_rate"]
#   h2h["over25_rate"]
#
# The current analyze_head_to_head() now returns:
#   home_wins
#   away_wins
#   draws
#   btts
#   over25
#
# Keeping this block for future reference in case
# we redesign the H2H engine later.

if h2h["winner"] == "HOME":

    add_score(scores, "Home Win", 8)
    add_score(scores, "Double Chance", 5)

elif h2h["winner"] == "AWAY":

    add_score(scores, "Away Win", 8)
    add_score(scores, "Double Chance", 5)

if h2h["btts_rate"] >= 0.60:

    add_score(scores, "BTTS", 8)

if h2h["over25_rate"] >= 0.60:

    add_score(scores, "Over 2.5 Goals", 8)
"""

    # Home / Away Specialist Engine
    home_ground_strength = calculate_home_away_strength(
    home_team_id,
    home_matches,
    home=True
    )

    away_ground_strength = calculate_home_away_strength(
    away_team_id,
    away_matches,
    home=False
    )

    # League Strength Engine

    home_league_strength = get_league_strength(
        home_matches[0]["competition"]["name"]
    ) if home_matches else 75

    away_league_strength = get_league_strength(
        away_matches[0]["competition"]["name"]
    ) if away_matches else 75

    home_rating += (home_league_strength - 75) * 0.20
    away_rating += (away_league_strength - 75) * 0.20

    # Motivation Engine
    motivation = calculate_motivation(match)

    home_rating += (motivation["home"] - 50) * 0.20
    away_rating += (motivation["away"] - 50) * 0.20

    # Weather Engine
    weather = calculate_weather(match)

    home_rating += (weather["home"] - 50) * 0.15
    away_rating += (weather["away"] - 50) * 0.15

    # Referee Engine
    referee = calculate_referee(match)

    home_rating += (referee["home"] - 50) * 0.10
    away_rating += (referee["away"] - 50) * 0.10

    # Home advantage / Away performance
    home_rating += (home_ground_strength - 50) * 0.30
    away_rating += (away_ground_strength - 50) * 0.30

    # ==============================
    # HOME / AWAY ENGINE VOTES
    # ==============================

    if home_ground_strength >= 75:
        homeaway_weight = weights["homeaway"]

        add_score(
            scores,
            "Home Win",
            8 * homeaway_weight
        )

    if away_ground_strength >= 75:
        add_score(scores, "Away Win", 8)

    if abs(home_ground_strength - away_ground_strength) <= 5:
        add_score(scores, "Double Chance", 4)

    # ==============================
    # LEAGUE STRENGTH ENGINE VOTES
    # ==============================

    league_weight = weights["league"]

    if home_league_strength > away_league_strength + 10:

        add_score(
            scores,
            "Home Win",
            6 * league_weight
        )

    elif away_league_strength > home_league_strength + 10:

        add_score(
            scores,
            "Away Win",
            6 * league_weight
        ) 

    # ==============================
    # MOTIVATION ENGINE VOTES
    # ==============================

    motivation_weight = weights["motivation"]

    if motivation["home"] >= 75:

        add_score(
        scores,
        "Home Win",
        6 * motivation_weight
    )

    if motivation["away"] >= 75:

        add_score(
        scores,
        "Away Win",
        6 * motivation_weight
    )     

    # ==============================
    # FATIGUE ENGINE VOTES
    # ==============================

    fatigue_weight = weights["fatigue"]

    if home_fatigue > away_fatigue + 10:

        add_score(
        scores,
        "Home Win",
        5 * fatigue_weight
    )

    elif away_fatigue > home_fatigue + 10:

        add_score(
        scores,
        "Away Win",
        5 * fatigue_weight
    )    

    # ==============================
    # SQUAD ENGINE VOTES
    # ==============================

    if squad["home"] > squad["away"] + 5:
        squad_weight = weights["squad"]

        add_score(
            scores,
            "Home Win",
            7 * squad_weight
        )

    elif squad["away"] > squad["home"] + 5:
        add_score(
            scores,
            "Away Win",
            7 * squad_weight
        ) 

    # ==============================
    # REFEREE ENGINE VOTES
    # ==============================

    referee_weight = weights["referee"]

    if referee["home"] > referee["away"] + 10:

        add_score(
        scores,
        "Home Win",
        3 * referee_weight
    )

    elif referee["away"] > referee["home"] + 10:

        add_score(
        scores,
        "Away Win",
        3 * referee_weight
    )
    difference = home_rating - away_rating

    signals = [

        home_form > away_form,
        home_attack > away_attack,
        home_defense > away_defense,
        home_rating > away_rating,
        home_fatigue > away_fatigue,
        squad["home"] > squad["away"]

    ]

    confidence = calculate_confidence(signals)

    prediction = choose_best_market(scores)

    odds_table = {
        "Home Win": 1.65,
        "Away Win": 1.80,
        "Draw": 3.20,
        "Double Chance": 1.40,
        "BTTS": 1.80,
        "Over 1.5 Goals": 1.45,
        "Over 2.5 Goals": 1.75,
        "Under 2.5 Goals": 1.70
    }

    odds = odds_table.get(prediction, 1.60)

    # -------------------------------
    # VALUE ENGINE
    # -------------------------------

    edge = calculate_value(
        confidence,
        odds
    )

    value = classify_value(edge)

    # -------------------------------
    # GRADE ENGINE
    # -------------------------------

    grade = calculate_prediction_grade(
        confidence,
        value
    )

    # -------------------------------
    # REASONING ENGINE
    # -------------------------------

    reasons = generate_reasoning(

        prediction,

        home_form,
        away_form,

        home_attack,
        away_attack,

        home_defense,
        away_defense,

        home_xg,
        away_xg,

        h2h,

        squad
    )

    return {

        "prediction": prediction,
        "confidence": confidence,

        "grade": grade,
        "value": value,
        "edge": edge,

        "reasoning": reasons,

        "odds": odds,

        "home_rating": round(home_rating, 2),
        "away_rating": round(away_rating, 2),

        # NEW
        "home_form": home_form,
        "away_form": away_form,

        "home_attack": home_attack,
        "away_attack": away_attack,

        "home_defense": home_defense,
        "away_defense": away_defense,

        "home_momentum": home_momentum,
        "away_momentum": away_momentum,

        "home_xg": round(home_xg["xg"], 2),
        "away_xg": round(away_xg["xg"], 2),

        "home_xga": round(home_xg["xga"], 2),
        "away_xga": round(away_xg["xga"], 2)
    }

if __name__ == "__main__":

    print("Prediction Engine Loaded Successfully ✅")