from database import (
    get_connection,
    record_engine_win,
    record_engine_loss
)

from engine_tracker import (
    record_engine_result
)

from dynamic_weights import (
    increase_weight,
    decrease_weight
)


def learn_from_finished_match(
    fixture_id,
    prediction,
    result
):
    """
    Learns from every finished match.

    prediction = Home Win / BTTS / etc
    result = WIN or LOSS
    """

    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""

        SELECT

            home_form,
            away_form,

            home_attack,
            away_attack,

            home_defense,
            away_defense,

            home_momentum,
            away_momentum,

            home_xg,
            away_xg,

            home_xga,
            away_xga

        FROM prediction_memory

        WHERE fixture_id=%s

    """, (fixture_id,))

    row = cur.fetchone()

    cur.close()
    conn.close()

    if not row:
        return

    (
        home_form,
        away_form,

        home_attack,
        away_attack,

        home_defense,
        away_defense,

        home_momentum,
        away_momentum,

        home_xg,
        away_xg,

        home_xga,
        away_xga

    ) = row

    correct = result == "WIN"

    # FORM ENGINE

    if home_form != away_form:

        record_engine_result(
           "form_engine",
        correct
    )

    if correct:
        increase_weight("form")
        record_engine_win("form")

    else:
        decrease_weight("form")
        record_engine_loss("form")

    # ATTACK ENGINE

    if home_attack != away_attack:

        record_engine_result(
            "attack_engine",
           correct
    )

    if correct:
        increase_weight("attack")
        record_engine_win("attack")

    else:
        decrease_weight("attack")

    # DEFENCE ENGINE

    if home_defense != away_defense:

        record_engine_result(
            "defense_engine",
           correct
    )

    if correct:
        increase_weight("defense")
        record_engine_win("defense")

    else:
        decrease_weight("defense")
        record_engine_loss("defense")

    # MOMENTUM

    if home_momentum != away_momentum:

        record_engine_result(
            "momentum_engine",
           correct
    )

    if correct:
        increase_weight("momentum")
        record_engine_win("momentum")

    else:
        decrease_weight("momentum")
        record_engine_loss("momentum")

    # xG

    if home_xg != away_xg:

        record_engine_result(
            "xg_engine",
           correct
    )

    if correct:
        increase_weight("xg")
        record_engine_win("xg")

    else:
        decrease_weight("xg")
        record_engine_loss("xg")

    # xGA

    if home_xga != away_xga:

        record_engine_result(
            "xga_engine",
           correct
    )

    if correct:
        increase_weight("xga")
        record_engine_win("xga")

    else:
        decrease_weight("xga")
        record_engine_loss("xga")

    print("AI learned from", fixture_id)


def learn_from_result(fixture_id, prediction, result):
    """
    Compatibility wrapper for result_checker.py
    """

    return learn_from_finished_match(
        fixture_id,
        prediction,
        result
    )


def process_finished_prediction(fixture_id, prediction, result):
    """
    Compatibility wrapper used by result_checker.py
    """

    return learn_from_finished_match(
        fixture_id,
        prediction,
        result
    )


if __name__ == "__main__":

    learn_from_finished_match(
        fixture_id=554935,
        prediction="Over 1.5 Goals",
        result="WIN"
    )