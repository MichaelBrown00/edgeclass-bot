import psycopg
from config import DATABASE_URL
from datetime import datetime


def get_connection():
    """
    Creates a PostgreSQL connection.
    """
    return psycopg.connect(DATABASE_URL)


def init_db():
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id BIGINT PRIMARY KEY,
            referral BIGINT,
            referrals INTEGER DEFAULT 0,
            plan TEXT DEFAULT 'free',
            expiry_date TEXT,
            joined_date TEXT,
            last_payment_reference TEXT,
            last_payment_amount INTEGER DEFAULT 0,
            last_payment_date TEXT
        )
    """)

    conn.commit()
    cur.close()
    conn.close()


def add_user(user_id, ref=None):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute(
        "SELECT user_id FROM users WHERE user_id=%s",
        (user_id,)
    )

    user = cur.fetchone()

    if user is None:

        cur.execute(
            """
            INSERT INTO users(user_id, referral)
            VALUES(%s, %s)
            """,
            (user_id, ref)
        )

        if ref:

            cur.execute(
                """
                UPDATE users
                SET referrals = referrals + 1
                WHERE user_id=%s
                """,
                (ref,)
            )

    conn.commit()
    cur.close()
    conn.close()


def get_referrals(user_id):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute(
        "SELECT referrals FROM users WHERE user_id=%s",
        (user_id,)
    )

    row = cur.fetchone()

    cur.close()
    conn.close()

    if row:
        return row[0]

    return 0


from datetime import datetime, timedelta


def update_plan(user_id, plan):
    conn = get_connection()
    cur = conn.cursor()

    joined = datetime.now()
    expiry = joined + timedelta(days=30)

    cur.execute(
        """
        UPDATE users
        SET
            plan=%s,
            joined_date=%s,
            expiry_date=%s
        WHERE user_id=%s
        """,
        (
            plan,
            joined.strftime("%Y-%m-%d"),
            expiry.strftime("%Y-%m-%d"),
            user_id
        )
    )

    conn.commit()
    cur.close()
    conn.close()


def get_plan(user_id):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute(
        """
        SELECT plan
        FROM users
        WHERE user_id=%s
        """,
        (user_id,)
    )

    row = cur.fetchone()

    cur.close()
    conn.close()

    if row:
        return row[0]

    return "free"

def get_plan(user_id):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute(
        "SELECT plan FROM users WHERE user_id=%s",
        (user_id,)
    )

    row = cur.fetchone()

    cur.close()
    conn.close()

    if row:
        return row[0]

    return "free"

def get_user(user_id):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute(
        """
        SELECT plan, joined_date, expiry_date
        FROM users
        WHERE user_id=%s
        """,
        (user_id,)
    )

    row = cur.fetchone()

    cur.close()
    conn.close()

    return row


def check_subscription(user_id):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute(
        """
        SELECT plan, expiry_date
        FROM users
        WHERE user_id=%s
        """,
        (user_id,)
    )

    row = cur.fetchone()

    if not row:
        cur.close()
        conn.close()
        return "free"

    plan, expiry = row

    if plan == "free":
        cur.close()
        conn.close()
        return "free"

    if expiry:

        expiry_date = datetime.strptime(
            expiry,
            "%Y-%m-%d"
        )

        if datetime.now() > expiry_date:

            cur.execute(
                """
                UPDATE users
                SET plan='free'
                WHERE user_id=%s
                """,
                (user_id,)
            )

            conn.commit()

            plan = "free"

    cur.close()
    conn.close()

    return plan


def get_user(user_id):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute(
        """
        SELECT
            plan,
            joined_date,
            expiry_date
        FROM users
        WHERE user_id=%s
        """,
        (user_id,)
    )

    row = cur.fetchone()

    cur.close()
    conn.close()

    return row


def get_expiry(user_id):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute(
        """
        SELECT expiry_date
        FROM users
        WHERE user_id=%s
        """,
        (user_id,)
    )

    row = cur.fetchone()

    cur.close()
    conn.close()

    if row:
        return row[0]

    return None