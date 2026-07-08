import sqlite3
from config import DB


def get_connection():
    """
    Creates a new database connection.
    """
    return sqlite3.connect(DB, timeout=20)


def init_db():
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS users(
        user_id INTEGER PRIMARY KEY,
        referral INTEGER,
        referrals INTEGER DEFAULT 0,
        plan TEXT DEFAULT 'free'
    )
    """)

    # Existing columns
    cur.execute("PRAGMA table_info(users)")
    existing_columns = [row[1] for row in cur.fetchall()]

    # Columns EdgeClass requires
    required_columns = {
        "plan": "TEXT DEFAULT 'free'",
        "expiry_date": "TEXT",
        "joined_date": "TEXT",
        "last_payment_reference": "TEXT",
        "last_payment_amount": "INTEGER DEFAULT 0",
        "last_payment_date": "TEXT"
    }

    for column, definition in required_columns.items():
        if column not in existing_columns:
            cur.execute(
                f"ALTER TABLE users ADD COLUMN {column} {definition}"
            )
            print(f"✅ Added missing column: {column}")

    conn.commit()
    conn.close()


def add_user(user_id, ref=None):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute(
        "SELECT user_id FROM users WHERE user_id=?",
        (user_id,)
    )

    user = cur.fetchone()

    if user is None:

        cur.execute(
            "INSERT INTO users(user_id, referral) VALUES(?, ?)",
            (user_id, ref)
        )

        if ref:

            cur.execute(
                """
                UPDATE users
                SET referrals = referrals + 1
                WHERE user_id=?
                """,
                (ref,)
            )

    conn.commit()
    conn.close()


def get_referrals(user_id):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute(
        "SELECT referrals FROM users WHERE user_id=?",
        (user_id,)
    )

    row = cur.fetchone()

    conn.close()

    if row:
        return row[0]

    return 0


def update_plan(user_id, plan):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute(
        """
        UPDATE users
        SET plan=?
        WHERE user_id=?
        """,
        (plan, user_id)
    )

    conn.commit()
    conn.close()


def get_plan(user_id):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute(
        "SELECT plan FROM users WHERE user_id=?",
        (user_id,)
    )

    row = cur.fetchone()

    conn.close()

    if row:
        return row[0]

    return "free"