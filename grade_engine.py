def calculate_prediction_grade(confidence, value_label):
    """
    Returns a star rating based on confidence
    and betting value.
    """

    if confidence >= 92 and value_label == "🔥 ELITE VALUE":
        return "★★★★★ ELITE PICK"

    elif confidence >= 87:
        return "★★★★☆ VERY STRONG"

    elif confidence >= 80:
        return "★★★☆☆ STRONG"

    elif confidence >= 72:
        return "★★☆☆☆ MODERATE"

    else:
        return "★☆☆☆☆ RISKY"