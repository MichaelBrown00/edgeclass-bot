from database import (
    get_connection
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

    else:
        decrease_weight("form")

    # ATTACK ENGINE

    if home_attack != away_attack:

        record_engine_result(
            "attack_engine",
           correct
    )

    if correct:
        increase_weight("attack")

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

    else:
        decrease_weight("defense")

    # MOMENTUM

    if home_momentum != away_momentum:

        record_engine_result(
            "momentum_engine",
           correct
    )

    if correct:
        increase_weight("momentum")

    else:
        decrease_weight("momentum")

    # xG

    if home_xg != away_xg:

        record_engine_result(
            "xg_engine",
           correct
    )

    if correct:
        increase_weight("xg")

    else:
        decrease_weight("xg")

    # xGA

    if home_xga != away_xga:

        record_engine_result(
            "xga_engine",
           correct
    )

    if correct:
        increase_weight("xga")

    else:
        decrease_weight("xga")

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