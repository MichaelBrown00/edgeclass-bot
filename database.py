import psycopg
from config import DATABASE_URL
from datetime import datetime, timedelta


def get_connection():
    """
    Creates a PostgreSQL connection.
    """
    return psycopg.connect(DATABASE_URL)


def init_db():
    remove_duplicate_predictions()
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id BIGINT PRIMARY KEY,
            referral BIGINT,
            referrals INTEGER DEFAULT 0,
            successful_referrals INTEGER DEFAULT 0,
            plan TEXT DEFAULT 'free',
            expiry_date TEXT,
            joined_date TEXT,
            last_payment_reference TEXT,
            last_payment_amount INTEGER DEFAULT 0,
            last_payment_date TEXT
        )
    """)

    cur.execute("""
        ALTER TABLE users
        ADD COLUMN IF NOT EXISTS successful_referrals INTEGER DEFAULT 0
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS predictions (

            id SERIAL PRIMARY KEY,

            match TEXT,

            prediction TEXT,

            confidence INTEGER,

            odds REAL,

            league TEXT,

            kickoff TEXT,

            prediction_date TEXT,

            status TEXT DEFAULT 'Pending',

            actual_score TEXT
        )
    """)

    cur.execute("""
    ALTER TABLE predictions
    ADD COLUMN IF NOT EXISTS fixture_id BIGINT
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


def get_successful_referrals(user_id):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute(
        """
        SELECT successful_referrals
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

    return 0


def downgrade_user(user_id):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute(
        """
        UPDATE users
SET
    plan='free',
    expiry_date=NULL,
    joined_date=NULL
WHERE user_id=%s
        """,
        (user_id,)
    )

    conn.commit()
    cur.close()
    conn.close()


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


def reward_referrer(user_id):
    conn = get_connection()
    cur = conn.cursor()

    # Find who referred this user
    cur.execute(
        """
        SELECT referral
        FROM users
        WHERE user_id=%s
        """,
        (user_id,)
    )

    row = cur.fetchone()

    if not row or row[0] is None:
        cur.close()
        conn.close()
        return

    referrer = row[0]

    # Increase successful referrals
    cur.execute(
        """
        UPDATE users
        SET successful_referrals = successful_referrals + 1
        WHERE user_id=%s
        """,
        (referrer,)
    )

    conn.commit()
    cur.close()
    conn.close()
    

def apply_referral_reward(user_id):
    """
    Automatically upgrades users based on successful referrals.
    """

    successful = get_successful_referrals(user_id)

    conn = get_connection()
    cur = conn.cursor()

    joined = datetime.now()

    if successful >= 20:

        cur.execute("""
            UPDATE users
            SET
                plan='vip',
                expiry_date=NULL
            WHERE user_id=%s
        """, (user_id,))

    elif successful >= 10:

        cur.execute("""
            UPDATE users
            SET
                plan='premium',
                expiry_date=NULL
            WHERE user_id=%s
        """, (user_id,))

    elif successful >= 5:

        expiry = joined + timedelta(days=30)

        cur.execute("""
            UPDATE users
            SET
                plan='vip',
                expiry_date=%s
            WHERE user_id=%s
        """, (
            expiry.strftime("%Y-%m-%d"),
            user_id
        ))

    elif successful >= 3:

        expiry = joined + timedelta(days=7)

        cur.execute("""
            UPDATE users
            SET
                plan='premium',
                expiry_date=%s
            WHERE user_id=%s
        """, (
            expiry.strftime("%Y-%m-%d"),
            user_id
        ))

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

# ---------------- ADMIN TESTING ----------------
def expire_user(user_id):
    conn = get_connection()
    cur = conn.cursor()

    yesterday = (
        datetime.now() - timedelta(days=1)
    ).strftime("%Y-%m-%d")

    cur.execute(
        """
        UPDATE users
        SET expiry_date=%s
        WHERE user_id=%s
        """,
        (yesterday, user_id)
    )

    conn.commit()

    cur.close()
    conn.close()


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

            cur.close()
            conn.close()

            downgrade_user(user_id)

            return "free"

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


def save_prediction(
    fixture_id,
    match,
    prediction,
    confidence,
    odds,
    league,
    kickoff
):
    conn = get_connection()
    cur = conn.cursor()

    # Check whether this fixture already exists
    cur.execute(
        """
        SELECT id
        FROM predictions
        WHERE fixture_id=%s
        """,
        (fixture_id,)
    )

    existing = cur.fetchone()

    if existing:

        cur.execute(
            """
            UPDATE predictions
            SET
                match=%s,
                prediction=%s,
                confidence=%s,
                odds=%s,
                league=%s,
                kickoff=%s,
                prediction_date=%s
            WHERE fixture_id=%s
            """,
            (
                match,
                prediction,
                confidence,
                odds,
                league,
                kickoff,
                datetime.now().strftime("%Y-%m-%d"),
                fixture_id
            )
        )

        print(f"🔄 Updated prediction {fixture_id}")

    else:

        cur.execute(
            """
            INSERT INTO predictions
            (
                fixture_id,
                match,
                prediction,
                confidence,
                odds,
                league,
                kickoff,
                prediction_date
            )
            VALUES
            (%s,%s,%s,%s,%s,%s,%s,%s)
            """,
            (
                fixture_id,
                match,
                prediction,
                confidence,
                odds,
                league,
                kickoff,
                datetime.now().strftime("%Y-%m-%d")
            )
        )

        print(f"✅ Saved new prediction {fixture_id}")

    conn.commit()

    cur.close()
    conn.close()


def remove_duplicate_predictions():

    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        DELETE FROM predictions
        WHERE id NOT IN (
            SELECT MAX(id)
            FROM predictions
            GROUP BY fixture_id
        );
    """)

    deleted = cur.rowcount

    conn.commit()

    cur.close()
    conn.close()

    print(f"🧹 Removed {deleted} duplicate predictions.")


def get_prediction_history(limit=10):

    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT
            match,
            prediction,
            confidence,
            odds,
            league,
            kickoff,
            status,
            actual_score
        FROM predictions
        ORDER BY id DESC
        LIMIT %s
    """, (limit,))

    rows = cur.fetchall()

    cur.close()
    conn.close()

    return rows


def debug_prediction_columns():
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT column_name
        FROM information_schema.columns
        WHERE table_name='predictions'
        ORDER BY ordinal_position;
    """)

    rows = cur.fetchall()

    print("====== PREDICTIONS TABLE ======")

    for row in rows:
        print(row[0])

    cur.close()
    conn.close()


def get_pending_predictions():

    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT
            id,
            fixture_id,
            match,
            prediction
        FROM predictions
        WHERE status='Pending'
    """)

    rows = cur.fetchall()

    cur.close()
    conn.close()

    return rows


def update_prediction_result(
    prediction_id,
    status,
    actual_score
):

    conn = get_connection()
    cur = conn.cursor()

    cur.execute(
        """
        UPDATE predictions
        SET
            status=%s,
            actual_score=%s
        WHERE id=%s
        """,
        (
            status,
            actual_score,
            prediction_id
        )
    )

    conn.commit()

    cur.close()
    conn.close()


def debug_predictions():
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT
            id,
            fixture_id,
            match
        FROM predictions
        ORDER BY id DESC
        LIMIT 20
    """)

    rows = cur.fetchall()

    for row in rows:
        print(row)

    cur.close()
    conn.close()


if __name__ == "__main__":
    debug_prediction_columns()