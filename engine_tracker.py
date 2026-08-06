import json
import os

FILE = "engine_scores.json"


def load_engine_scores():

    if not os.path.exists(FILE):

        return {}

    with open(FILE, "r") as f:

        return json.load(f)


def save_engine_scores(data):

    with open(FILE, "w") as f:

        json.dump(data, f, indent=4)


def record_engine_result(engine_name, correct):

    data = load_engine_scores()

    if engine_name not in data:

        data[engine_name] = {

            "correct": 0,
            "wrong": 0

        }

    if correct:

        data[engine_name]["correct"] += 1

    else:

        data[engine_name]["wrong"] += 1

    save_engine_scores(data)


def get_accuracy(engine_name):

    data = load_engine_scores()

    if engine_name not in data:

        return 0.75

    c = data[engine_name]["correct"]
    w = data[engine_name]["wrong"]

    total = c + w

    if total == 0:

        return 0.75

    return c / total