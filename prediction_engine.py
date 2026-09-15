"""
==========================================
EDGECLASS AI V2
Prediction Engine
==========================================
"""

from collections import Counter
import config
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
    EdgeClass Prediction Engine V2

    Pipeline:
        Evidence
        -> Market Scoring
        -> Best Market
        -> Market-specific Confidence
        -> Data Quality
        -> Value
        -> Grade
        -> Market-specific Reasoning
    """

    # ============================================================
    # 1. INITIALIZE
    # ============================================================

    scores = initialize_market_scores()

    weights = get_dynamic_weights()

    # Make sure all learned weight values are numeric.
    #
    # weights.json stores learned weights around 10.0.
    # Keep the actual learned values here.
    # Convert them to scoring multipliers exactly once below.
    form_weight = float(weights.get("form", 10.0))
    attack_weight = float(weights.get("attack", 10.0))
    defense_weight = float(weights.get("defense", 10.0))
    momentum_weight = float(weights.get("momentum", 10.0))
    xg_weight = float(weights.get("xg", 10.0))
    xga_weight = float(weights.get("xga", 10.0))
    h2h_weight = float(weights.get("h2h", 10.0))
    squad_weight = float(weights.get("squad", 10.0))
    league_weight = float(weights.get("league", 10.0))
    motivation_weight = float(weights.get("motivation", 10.0))
    fatigue_weight = float(weights.get("fatigue", 10.0))
    referee_weight = float(weights.get("referee", 10.0))
    homeaway_weight = float(weights.get("homeaway", 10.0))

    # Normalize learned weights around 10.0.
    # Example: 10.25 -> 1.025.
    form_multiplier = form_weight / 10.0
    attack_multiplier = attack_weight / 10.0
    defense_multiplier = defense_weight / 10.0
    momentum_multiplier = momentum_weight / 10.0
    xg_multiplier = xg_weight / 10.0
    xga_multiplier = xga_weight / 10.0
    h2h_multiplier = h2h_weight / 10.0
    squad_multiplier = squad_weight / 10.0
    league_multiplier = league_weight / 10.0
    motivation_multiplier = motivation_weight / 10.0
    fatigue_multiplier = fatigue_weight / 10.0
    referee_multiplier = referee_weight / 10.0
    homeaway_multiplier = homeaway_weight / 10.0

    # ============================================================
    # 2. EVIDENCE ENGINES
    # ============================================================

    home_form = calculate_form(
        home_team_id,
        home_matches
    )

    away_form = calculate_form(
        away_team_id,
        away_matches
    )

    home_attack = calculate_attack(
        home_team_id,
        home_matches
    )

    away_attack = calculate_attack(
        away_team_id,
        away_matches
    )

    home_defense = calculate_defense(
        home_team_id,
        home_matches
    )

    away_defense = calculate_defense(
        away_team_id,
        away_matches
    )

    home_momentum = calculate_recent_momentum(
        home_team_id,
        home_matches
    )

    away_momentum = calculate_recent_momentum(
        away_team_id,
        away_matches
    )

    # ============================================================
    # 3. TEAM RATINGS
    # ============================================================

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

    # Squad strength
    squad = calculate_squad_strength(
        home_team_id,
        away_team_id
    )

    home_rating += (
        squad["home"] - SQUAD_BASELINE
    ) * 0.25

    away_rating += (
        squad["away"] - SQUAD_BASELINE
    ) * 0.25

    # Fatigue
    home_fatigue = calculate_fatigue(home_matches)
    away_fatigue = calculate_fatigue(away_matches)

    home_rating += (
        home_fatigue - 85
    ) * 0.20

    away_rating += (
        away_fatigue - 85
    ) * 0.20

    # ============================================================
    # 4. ESTIMATED GOAL METRICS
    # ============================================================
    #
    # NOTE:
    # calculate_expected_goals() currently calculates goal-based
    # estimates rather than provider-grade statistical xG.
    # We preserve the existing interface for V2 compatibility.
    #

    home_xg = calculate_expected_goals(
        home_team_id,
        home_matches
    )

    away_xg = calculate_expected_goals(
        away_team_id,
        away_matches
    )

    home_rating += home_xg["xg"] * 3
    away_rating += away_xg["xg"] * 3

    home_rating -= home_xg["xga"] * 2 * xga_multiplier
    away_rating -= away_xg["xga"] * 2 * xga_multiplier

    # ============================================================
    # 5. HEAD-TO-HEAD
    # ============================================================

    h2h = analyze_head_to_head(
        home_team_id,
        away_team_id
    )

    # ============================================================
    # 6. HOME / AWAY
    # ============================================================

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

    # ============================================================
    # 7. LEAGUE STRENGTH
    # ============================================================

    home_league_strength = (
        get_league_strength(
            home_matches[0]["competition"]["name"]
        )
        if home_matches
        else 75
    )

    away_league_strength = (
        get_league_strength(
            away_matches[0]["competition"]["name"]
        )
        if away_matches
        else 75
    )

    home_rating += (
        home_league_strength - 75
    ) * 0.20

    away_rating += (
        away_league_strength - 75
    ) * 0.20

    # ============================================================
    # 8. MOTIVATION / WEATHER / REFEREE
    # ============================================================

    motivation = calculate_motivation(match)
    weather = calculate_weather(match)
    referee = calculate_referee(match)

    home_rating += (
        motivation["home"] - 50
    ) * 0.20

    away_rating += (
        motivation["away"] - 50
    ) * 0.20

    home_rating += (
        weather["home"] - 50
    ) * 0.15

    away_rating += (
        weather["away"] - 50
    ) * 0.15

    home_rating += (
        referee["home"] - 50
    ) * 0.10

    away_rating += (
        referee["away"] - 50
    ) * 0.10

    # Home / away performance adjustment
    home_rating += (
        home_ground_strength - 50
    ) * 0.30

    away_rating += (
        away_ground_strength - 50
    ) * 0.30

    # ============================================================
    # 9. MARKET SCORING
    # ============================================================

    # ------------------------------------------------------------
    # FORM
    # ------------------------------------------------------------

    if home_form > away_form:
        add_score(
            scores,
            "Home Win",
            12 * form_multiplier
        )

        add_score(
            scores,
            "Double Chance",
            6
        )

    elif away_form > home_form:
        add_score(
            scores,
            "Away Win",
            12 * form_multiplier
        )

        add_score(
            scores,
            "Double Chance",
            6
        )

    else:
        add_score(
            scores,
            "Draw",
            8
        )

    # ------------------------------------------------------------
    # ATTACK
    # ------------------------------------------------------------

    if home_attack >= 80:
        add_score(
            scores,
            "Home Win",
            10 * attack_multiplier
        )

        add_score(
            scores,
            "Over 2.5 Goals",
            6
        )

    if away_attack >= 80:
        add_score(
            scores,
            "Away Win",
            10 * attack_multiplier
        )

        add_score(
            scores,
            "Over 2.5 Goals",
            6
        )

    if home_attack >= 75 and away_attack >= 75:
        add_score(
            scores,
            "BTTS",
            12
        )

        add_score(
            scores,
            "Over 2.5 Goals",
            10
        )

    elif home_attack >= 70 or away_attack >= 70:
        add_score(
            scores,
            "Over 1.5 Goals",
            8
        )

    # ------------------------------------------------------------
    # DEFENSE
    # ------------------------------------------------------------

    if home_defense >= 80 and away_defense >= 80:
        add_score(
            scores,
            "Under 2.5 Goals",
            12 * defense_multiplier
        )

        add_score(
            scores,
            "Double Chance",
            6
        )

    elif home_defense <= 60 and away_defense <= 60:
        add_score(
            scores,
            "BTTS",
            10
        )

        add_score(
            scores,
            "Over 2.5 Goals",
            10
        )

    elif home_defense <= 60 or away_defense <= 60:
        add_score(
            scores,
            "Over 1.5 Goals",
            8
        )

    # ------------------------------------------------------------
    # MOMENTUM
    # ------------------------------------------------------------

    if home_momentum >= 80:
        add_score(
            scores,
            "Home Win",
            10 * momentum_multiplier
        )

    if away_momentum >= 80:
        add_score(
            scores,
            "Away Win",
            10 * momentum_multiplier
        )

    if abs(home_momentum - away_momentum) <= 5:
        add_score(
            scores,
            "Double Chance",
            6
        )

    # ------------------------------------------------------------
    # ESTIMATED GOAL METRICS
    # ------------------------------------------------------------

    if home_xg["xg"] >= 2.0:
        add_score(
            scores,
            "Home Win",
            10 * xg_multiplier
        )

        add_score(
            scores,
            "Over 2.5 Goals",
            8
        )

    if away_xg["xg"] >= 2.0:
        add_score(
            scores,
            "Away Win",
            10 * xg_multiplier
        )

        add_score(
            scores,
            "Over 2.5 Goals",
            8
        )

    if (
        home_xg["xg"] >= 1.5
        and away_xg["xg"] >= 1.5
    ):
        add_score(
            scores,
            "BTTS",
            12
        )

    if (
        home_xg["xga"] >= 1.6
        or away_xg["xga"] >= 1.6
    ):
        add_score(
            scores,
            "Over 2.5 Goals",
            8
        )

    # ------------------------------------------------------------
    # H2H
    # ------------------------------------------------------------

    if h2h["home_wins"] > h2h["away_wins"]:
        add_score(
            scores,
            "Home Win",
            8 * h2h_multiplier
        )

        add_score(
            scores,
            "Double Chance",
            5
        )

    elif h2h["away_wins"] > h2h["home_wins"]:
        add_score(
            scores,
            "Away Win",
            8 * h2h_multiplier
        )

        add_score(
            scores,
            "Double Chance",
            5
        )

    if h2h["draws"] >= 2:
        add_score(
            scores,
            "Draw",
            6
        )

    if h2h["btts"] >= 3:
        add_score(
            scores,
            "BTTS",
            8
        )

    if h2h["over25"] >= 3:
        add_score(
            scores,
            "Over 2.5 Goals",
            8
        )

    # ------------------------------------------------------------
    # HOME / AWAY ENGINE
    # ------------------------------------------------------------

    if home_ground_strength >= 75:
        add_score(
            scores,
            "Home Win",
            8 * homeaway_multiplier
        )

    if away_ground_strength >= 75:
        add_score(
            scores,
            "Away Win",
            8 * homeaway_multiplier
        )

    if abs(
        home_ground_strength - away_ground_strength
    ) <= 5:
        add_score(
            scores,
            "Double Chance",
            4
        )

    # ------------------------------------------------------------
    # LEAGUE STRENGTH
    # ------------------------------------------------------------

    if (
        home_league_strength
        > away_league_strength + 10
    ):
        add_score(
            scores,
            "Home Win",
            6 * league_multiplier
        )

    elif (
        away_league_strength
        > home_league_strength + 10
    ):
        add_score(
            scores,
            "Away Win",
            6 * league_multiplier
        )

    # ------------------------------------------------------------
    # MOTIVATION
    # ------------------------------------------------------------

    if motivation["home"] >= 75:
        add_score(
            scores,
            "Home Win",
            6 * motivation_multiplier
        )

    if motivation["away"] >= 75:
        add_score(
            scores,
            "Away Win",
            6 * motivation_multiplier
        )

    # ------------------------------------------------------------
    # FATIGUE
    # ------------------------------------------------------------

    if home_fatigue > away_fatigue + 10:
        add_score(
            scores,
            "Home Win",
            5 * fatigue_multiplier
        )

    elif away_fatigue > home_fatigue + 10:
        add_score(
            scores,
            "Away Win",
            5 * fatigue_multiplier
        )

    # ------------------------------------------------------------
    # SQUAD
    # ------------------------------------------------------------

    if squad["home"] > squad["away"] + 5:
        add_score(
            scores,
            "Home Win",
            7 * squad_multiplier
        )

    elif squad["away"] > squad["home"] + 5:
        add_score(
            scores,
            "Away Win",
            7 * squad_multiplier
        )

    # ------------------------------------------------------------
    # REFEREE
    # ------------------------------------------------------------

    if referee["home"] > referee["away"] + 10:
        add_score(
            scores,
            "Home Win",
            3 * referee_multiplier
        )

    elif referee["away"] > referee["home"] + 10:
        add_score(
            scores,
            "Away Win",
            3 * referee_multiplier
        )

    # ============================================================
    # 10. TEAM-RATING VOTE
    # ============================================================

    rating_difference = home_rating - away_rating

    if rating_difference >= 8:
        add_score(
            scores,
            "Home Win",
            10
        )

    elif rating_difference <= -8:
        add_score(
            scores,
            "Away Win",
            10
        )

    elif abs(rating_difference) <= 3:
        add_score(
            scores,
            "Draw",
            6
        )

    # ============================================================
    # 11. SELECT BEST MARKET
    # ============================================================

    ranked_markets = sorted(
        scores.items(),
        key=lambda item: item[1],
        reverse=True
    )

    prediction = ranked_markets[0][0]
    best_score = ranked_markets[0][1]

    second_score = (
        ranked_markets[1][1]
        if len(ranked_markets) > 1
        else 0
    )

    # ============================================================
    # 12. MARKET-SPECIFIC CONFIDENCE
    # ============================================================
    #
    # Confidence is now based on:
    #   - support for the selected market
    #   - separation from the second-best market
    #
    # It is NOT based on "is the home team stronger?"
    #

    if best_score <= 0:
        market_confidence = 50
    else:
        dominance = (
            (best_score - second_score)
            / best_score
        )

        dominance = max(
            0.0,
            min(1.0, dominance)
        )

        market_confidence = (
            55
            + dominance * 40
        )

    # ============================================================
    # 13. DATA QUALITY
    # ============================================================

    home_sample = min(
        len(home_matches),
        5
    )

    away_sample = min(
        len(away_matches),
        5
    )

    sample_quality = (
        (home_sample + away_sample)
        / 10
    )

    sample_quality = max(
        0.0,
        min(1.0, sample_quality)
    )

    # Full five-match samples preserve confidence.
    # Smaller samples receive a modest penalty.
    quality_penalty = (
        1.0 - sample_quality
    ) * 10

    confidence = round(
        max(
            50,
            min(
                95,
                market_confidence - quality_penalty
            )
        )
    )

    # ============================================================
    # 14. ODDS
    # ============================================================
    #
    # These remain placeholders until a genuine odds provider
    # is connected. They are NOT treated as live bookmaker odds.
    #

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

    odds = odds_table.get(
        prediction,
        1.60
    )

    # ============================================================
    # 15. VALUE
    # ============================================================

    edge = calculate_value(
        confidence,
        odds
    )

    value = classify_value(edge)

    # ============================================================
    # 16. GRADE
    # ============================================================

    grade = calculate_prediction_grade(
        confidence,
        value
    )

    # ============================================================
    # 17. MARKET-SPECIFIC REASONING
    # ============================================================

    reasons = []

    if prediction == "Home Win":

        if home_form > away_form:
            reasons.append(
                "Home team has the stronger recent form."
            )

        if home_attack > away_attack:
            reasons.append(
                "Home team has the stronger attacking profile."
            )

        if home_defense > away_defense:
            reasons.append(
                "Home team has the stronger defensive profile."
            )

        if home_momentum > away_momentum:
            reasons.append(
                "Recent momentum favours the home team."
            )

        if home_rating > away_rating:
            reasons.append(
                "Overall team rating favours the home side."
            )

        if h2h["home_wins"] > h2h["away_wins"]:
            reasons.append(
                "Historical meetings favour the home side."
            )

    elif prediction == "Away Win":

        if away_form > home_form:
            reasons.append(
                "Away team has the stronger recent form."
            )

        if away_attack > home_attack:
            reasons.append(
                "Away team has the stronger attacking profile."
            )

        if away_defense > home_defense:
            reasons.append(
                "Away team has the stronger defensive profile."
            )

        if away_momentum > home_momentum:
            reasons.append(
                "Recent momentum favours the away team."
            )

        if away_rating > home_rating:
            reasons.append(
                "Overall team rating favours the away side."
            )

        if h2h["away_wins"] > h2h["home_wins"]:
            reasons.append(
                "Historical meetings favour the away side."
            )

    elif prediction == "Draw":

        if abs(home_rating - away_rating) <= 3:
            reasons.append(
                "Overall team ratings are closely matched."
            )

        if abs(home_form - away_form) <= 5:
            reasons.append(
                "Recent form is closely matched."
            )

        if h2h["draws"] >= 2:
            reasons.append(
                "Recent head-to-head history contains multiple draws."
            )

    elif prediction == "Double Chance":

        if abs(home_rating - away_rating) <= 8:
            reasons.append(
                "The teams are relatively close on overall rating."
            )

        if abs(home_momentum - away_momentum) <= 5:
            reasons.append(
                "Recent momentum is closely matched."
            )

        if abs(
            home_ground_strength
            - away_ground_strength
        ) <= 5:
            reasons.append(
                "Home/away performance is closely matched."
            )

    elif prediction == "BTTS":

        if (
            home_attack >= 75
            and away_attack >= 75
        ):
            reasons.append(
                "Both teams show strong attacking profiles."
            )

        if (
            home_xg["xg"] >= 1.5
            and away_xg["xg"] >= 1.5
        ):
            reasons.append(
                "Both teams have strong estimated goal output."
            )

        if h2h["btts"] >= 3:
            reasons.append(
                "Head-to-head history supports both teams scoring."
            )

    elif prediction == "Over 1.5 Goals":

        if home_attack >= 70 or away_attack >= 70:
            reasons.append(
                "At least one attack shows strong scoring potential."
            )

        if (
            home_defense <= 60
            or away_defense <= 60
        ):
            reasons.append(
                "At least one defense has shown vulnerability."
            )

    elif prediction == "Over 2.5 Goals":

        if (
            home_attack >= 75
            and away_attack >= 75
        ):
            reasons.append(
                "Both teams show strong attacking profiles."
            )

        if (
            home_xg["xg"] >= 2.0
            or away_xg["xg"] >= 2.0
        ):
            reasons.append(
                "Estimated goal output supports a high-scoring match."
            )

        if (
            home_defense <= 60
            and away_defense <= 60
        ):
            reasons.append(
                "Both defenses show vulnerability."
            )

        if h2h["over25"] >= 3:
            reasons.append(
                "Head-to-head history supports higher scoring."
            )

    elif prediction == "Under 2.5 Goals":

        if (
            home_defense >= 80
            and away_defense >= 80
        ):
            reasons.append(
                "Both teams show strong defensive profiles."
            )

        if (
            home_xg["xga"] < 1.6
            and away_xg["xga"] < 1.6
        ):
            reasons.append(
                "Estimated defensive goal-concession rates are controlled."
            )

    if not reasons:
        reasons.append(
            "The selected market received the strongest combined support from the available evidence."
        )

    # ============================================================
    # 18. RETURN COMPLETE PREDICTION SNAPSHOT
    # ============================================================

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

        "home_form": home_form,
        "away_form": away_form,

        "home_attack": home_attack,
        "away_attack": away_attack,

        "home_defense": home_defense,
        "away_defense": away_defense,

        "home_momentum": home_momentum,
        "away_momentum": away_momentum,

        "home_xg": home_xg["xg"],
        "away_xg": away_xg["xg"],

        "home_xga": home_xg["xga"],
        "away_xga": away_xg["xga"],

        "form_weight": form_weight,
        "attack_weight": attack_weight,
        "defense_weight": defense_weight,
        "momentum_weight": momentum_weight,
        "xg_weight": xg_weight,
        "xga_weight": float(
            weights.get("xga", 10.0)
        ),
        "h2h_weight": h2h_weight,
        "squad_weight": squad_weight,
        "league_weight": league_weight,
        "motivation_weight": motivation_weight,
        "fatigue_weight": fatigue_weight,
        "referee_weight": referee_weight,
        "homeaway_weight": homeaway_weight,

        "market_scores": scores,

        "data_quality": round(
            sample_quality * 100,
            2
        )
    }

if __name__ == "__main__":

    print("Prediction Engine Loaded Successfully ✅")