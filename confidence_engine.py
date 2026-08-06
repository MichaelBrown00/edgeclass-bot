"""
EDGECLASS AI

Confidence Engine
Version 1
"""


def calculate_confidence(signals):
    """
    signals = list of True/False values.

    True means the signal supports
    the prediction.

    Returns confidence between
    50 and 95.
    """

    total = len(signals)

    if total == 0:
        return 50

    agreement = sum(signals)

    confidence = 50 + (agreement / total) * 45

    return round(min(confidence, 95))