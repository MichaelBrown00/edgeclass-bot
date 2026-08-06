from database import get_connection


def get_prediction_stats():
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT
            COUNT(*) AS total,
            SUM(CASE WHEN status='WIN' THEN 1 ELSE 0 END) AS wins,
            SUM(CASE WHEN status='LOSS' THEN 1 ELSE 0 END) AS losses
        FROM predictions
    """)

    total, wins, losses = cur.fetchone()

    total = total or 0
    wins = wins or 0
    losses = losses or 0

    strike_rate = 0

    if total > 0:
        strike_rate = round((wins / total) * 100, 1)

    cur.close()
    conn.close()

    return {
        "total": total,
        "wins": wins,
        "losses": losses,
        "strike_rate": strike_rate
    }