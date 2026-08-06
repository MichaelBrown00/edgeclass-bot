import json
import os

WEIGHTS_FILE = "weights.json"

DEFAULT_WEIGHTS = {

    "form": 10,

    "attack": 10,

    "defense": 10,

    "momentum": 10,

    "xg": 10,

    "xga": 10,

    "h2h": 10,

    "squad": 10,

    "league": 10,

    "motivation": 10,

    "fatigue": 10,

    "referee": 10,

    "homeaway": 10

}


from database import get_connection

def load_dynamic_weights():
    """
    Loads the latest learned weights.

    Currently this is just an alias to load_weights().
    """

    return load_weights()


def load_weights():

    if not os.path.exists(WEIGHTS_FILE):

        save_weights(DEFAULT_WEIGHTS)

        return DEFAULT_WEIGHTS.copy()

    with open(WEIGHTS_FILE, "r") as f:

        weights = json.load(f)

    # Automatically add any new engines

    updated = False

    for key, value in DEFAULT_WEIGHTS.items():

        if key not in weights:

            weights[key] = value

            updated = True

    if updated:

        save_weights(weights)

    return weights


def save_weights(weights):
    """
    Saves all engine weights.
    """

    with open(WEIGHTS_FILE, "w") as f:

        json.dump(weights, f, indent=4)


def increase_weight(engine, amount=0.25):
    """
    Reward an engine.
    """

    weights = load_weights()

    if engine in weights:

        weights[engine] = min(
            30,
            round(weights[engine] + amount, 2)
        )

    save_weights(weights)


def decrease_weight(engine, amount=0.25):
    """
    Penalize an engine.
    """

    weights = load_weights()

    if engine in weights:

        weights[engine] = max(
            5,
            round(weights[engine] - amount, 2)
        )

    save_weights(weights)


def get_weight(engine):
    """
    Returns one engine's weight.
    """

    weights = load_weights()

    return weights.get(engine, 10)


def get_dynamic_weights():
    """
    Returns the entire weight dictionary.

    Used inside prediction_engine.py.
    """

    return load_weights()


if __name__ == "__main__":

    print("Current Dynamic Weights:\n")

    weights = get_dynamic_weights()

    for engine, value in weights.items():

        print(f"{engine:<12} : {value}")
      