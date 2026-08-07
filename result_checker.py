from football_api import get_fixture_by_id
from database import get_connection
from database import get_pending_predictions

from database import update_prediction_result
from database import save_prediction_memory
from learning_engine import learn_from_finished_match

def check_finished_predictions():

    print("Checking pending predictions...")

    pending_predictions = get_pending_predictions()

    print(f"Pending predictions: {len(pending_predictions)}")

    for prediction in pending_predictions:

        fixture_id = prediction[10]

        fixture = get_fixture_by_id(fixture_id)

        if fixture is None:
            continue

        winner = fixture["score"]["winner"]

        print(f"{fixture_id} -> Winner: {winner}")

        if winner is None:
            continue

        home = fixture["homeTeam"]["name"]
        away = fixture["awayTeam"]["name"]

        home_goals = fixture["score"]["fullTime"]["home"]
        away_goals = fixture["score"]["fullTime"]["away"]

        print(
            f"{home} {home_goals}-{away_goals} {away}"
        )

        prediction_text = prediction[2]

        print(f"Prediction: {prediction_text}")

        # Determine actual winner

        total_goals = home_goals + away_goals

        if prediction_text == "Home Win":

            prediction_result = (
                "WIN" if home_goals > away_goals else "LOSS"
            )

        elif prediction_text == "Away Win":

            prediction_result = (
                "WIN" if away_goals > home_goals else "LOSS"
            )

        elif prediction_text == "Draw":

            prediction_result = (
                "WIN" if home_goals == away_goals else "LOSS"
            )

        elif prediction_text == "Over 1.5 Goals":

            prediction_result = (
                "WIN" if total_goals >= 2 else "LOSS"
            )

        elif prediction_text == "Over 2.5 Goals":

            prediction_result = (
                "WIN" if total_goals >= 3 else "LOSS"
            )

        elif prediction_text == "BTTS Yes":

            prediction_result = (
                "WIN" if home_goals > 0 and away_goals > 0 else "LOSS"
            )

        else:

            prediction_result = "UNKNOWN"

        print(f"Prediction Result: {prediction_result}")

        prediction_id = prediction[0]

        actual_score = f"{home_goals}-{away_goals}"

        update_prediction_result(
            prediction_id,
            prediction_result,
            actual_score
        )

        prediction_memory = {
            "prediction_date": prediction[7],
            "match": prediction[1],
            "league": prediction[5],
            "prediction": prediction[2],
            "confidence": prediction[3],

            "grade": None,
            "value": None,
            "edge": None,
            "reasoning": None,

            "home_rating": None,
            "away_rating": None,

            "home_form": None,
            "away_form": None,

            "home_attack": None,
            "away_attack": None,

            "home_defense": None,
            "away_defense": None,

            "home_momentum": None,
            "away_momentum": None,

            "home_xg": None,
            "away_xg": None,

            "home_xga": None,
            "away_xga": None,
        }

        save_prediction_memory(
            fixture_id,
            prediction_memory
        )

        print("Prediction stored in AI memory.")

        learn_from_finished_match(
            fixture_id,
            prediction_text,
            prediction_result
        )

        print("Prediction database updated.")

if __name__ == "__main__":
    check_finished_predictions()        