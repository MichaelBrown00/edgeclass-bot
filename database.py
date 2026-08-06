import psycopg
from config import DATABASE_URL
from datetime import datetime, timedelta


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

            actual_score TEXT,

            tier TEXT DEFAULT 'premium'
        )
    """)

    cur.execute("""
    ALTER TABLE predictions
    ADD COLUMN IF NOT EXISTS fixture_id BIGINT
""")
    
    cur.execute("""
    ALTER TABLE predictions
    ADD COLUMN IF NOT EXISTS tier TEXT DEFAULT 'premium'
""")

    cur.execute("""
    ALTER TABLE predictions
    ADD COLUMN IF NOT EXISTS grade TEXT,
    ADD COLUMN IF NOT EXISTS value TEXT,
    ADD COLUMN IF NOT EXISTS edge REAL,
    ADD COLUMN IF NOT EXISTS reasoning TEXT,
    ADD COLUMN IF NOT EXISTS home_rating REAL,
    ADD COLUMN IF NOT EXISTS away_rating REAL;
""")

    cur.execute("""
    CREATE TABLE IF NOT EXISTS prediction_memory (

        id SERIAL PRIMARY KEY,

        fixture_id BIGINT UNIQUE,

        prediction_date TEXT,

        match TEXT,

        league TEXT,

        prediction TEXT,

        confidence INTEGER,

        grade TEXT,

        value TEXT,

        edge REAL,

        result TEXT,

        actual_score TEXT,

        home_rating REAL,
        away_rating REAL,

        home_form REAL,
        away_form REAL,

        home_attack REAL,
        away_attack REAL,

        home_defense REAL,
        away_defense REAL,

        home_momentum REAL,
        away_momentum REAL,

        home_xg REAL,
        away_xg REAL,

        home_xga REAL,
        away_xga REAL,

        form_weight REAL,

        attack_weight REAL,

        defense_weight REAL,

        momentum_weight REAL,

        xg_weight REAL,

        xga_weight REAL,

        h2h_weight REAL,

        squad_weight REAL,

        league_weight REAL,

        motivation_weight REAL,

        fatigue_weight REAL,

        referee_weight REAL,

        homeaway_weight REAL,

        reasoning TEXT,
        
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
""")
    
    conn.commit()
    cur.close()
    conn.close()


def todays_predictions_exist():

    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT COUNT(*)
        FROM predictions
        WHERE prediction_date=%s
    """, (
        datetime.now().strftime("%Y-%m-%d"),
    ))

    count = cur.fetchone()[0]

    cur.close()
    conn.close()

    return count > 0


def get_todays_predictions():

    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT
            fixture_id,
            match,
            prediction,
            confidence,
            odds,
            league,
            kickoff
        FROM predictions
        WHERE prediction_date=%s
        ORDER BY confidence DESC
    """, (
        datetime.now().strftime("%Y-%m-%d"),
    ))

    rows = cur.fetchall()

    cur.close()
    conn.close()

    return rows


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
    kickoff,
    grade,
    value,
    edge,
    reasoning,
    home_rating,
    away_rating,
    tier="premium"
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

    print(f"fixture_id={fixture_id}, existing={existing}")

    if fixture_id is None:
        print("❌ Cannot save prediction without fixture_id.")
        cur.close()
        conn.close()
        return

    if existing:

        prediction_data = {

            "prediction_date": datetime.now().strftime("%Y-%m-%d"),

            "match": match,
            "league": league,

            "prediction": prediction,
            "confidence": confidence,

            "grade": grade,
            "value": value,
            "edge": edge,
            "reasoning": reasoning,

            "home_rating": home_rating,
            "away_rating": away_rating

        }

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
                prediction_date=%s,
                grade=%s,
                value=%s,
                edge=%s,
                reasoning=%s,
                home_rating=%s,
                away_rating=%s,
                tier=%s
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
                grade,
                value,
                edge,
                reasoning,
                home_rating,
                away_rating,
                tier,
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

                grade,
                value,
                edge,
                reasoning,
                home_rating,
                away_rating,

                prediction_date,
                tier
            )
            VALUES
            (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
            """,
            (
                fixture_id,
                match,
                prediction,
                confidence,
                odds,
                league,
                kickoff,

                grade,
                value,
                edge,
                reasoning,
                home_rating,
                away_rating,

                datetime.now().strftime("%Y-%m-%d"),
                tier
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


def get_pending_predictions():
    """
    Returns every pending prediction.
    """

    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT *
        FROM predictions
        WHERE status='Pending'
        AND fixture_id IS NOT NULL
    """)

    rows = cur.fetchall()

    cur.close()
    conn.close()

    return rows


def get_prediction_history(plan, limit=10):

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
            actual_score,
            tier
        FROM predictions
        WHERE tier=%s
        ORDER BY id DESC
        LIMIT %s
    """, (plan, limit,))

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


def update_prediction_result(
    prediction_id,
    result,
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
            result,
            actual_score,
            prediction_id
        )
    )

    conn.commit()

    cur.close()
    conn.close()


def save_prediction_memory(
    fixture_id,
    prediction_data
):

    conn = get_connection()
    cur = conn.cursor()

    cur.execute(
    """
    INSERT INTO prediction_memory (
        fixture_id,
        prediction_date,
        match,
        league,
        prediction,
        confidence,
        grade,
        value,
        edge,
        reasoning,

        home_rating,
        away_rating,

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
    )
    VALUES (
        %s,%s,%s,%s,%s,%s,%s,%s,%s,%s,
        %s,%s,
        %s,%s,
        %s,%s,
        %s,%s,
        %s,%s,
        %s,%s,
        %s,%s
    )
    """,
    (
        fixture_id,
        prediction_data["prediction_date"],
        prediction_data["match"],
        prediction_data["league"],
        prediction_data["prediction"],
        prediction_data["confidence"],
        prediction_data["grade"],
        prediction_data["value"],
        prediction_data["edge"],
        prediction_data["reasoning"],

        prediction_data["home_rating"],
        prediction_data["away_rating"],

        prediction_data["home_form"],
        prediction_data["away_form"],

        prediction_data["home_attack"],
        prediction_data["away_attack"],

        prediction_data["home_defense"],
        prediction_data["away_defense"],

        prediction_data["home_momentum"],
        prediction_data["away_momentum"],

        prediction_data["home_xg"],
        prediction_data["away_xg"],

        prediction_data["home_xga"],
        prediction_data["away_xga"]
    )
)

    conn.commit()

    cur.close()
    conn.close()    


def get_prediction_history(limit=300):

    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""

        SELECT *

        FROM prediction_memory

        ORDER BY created_at DESC

        LIMIT %s

    """, (limit,))

    rows = cur.fetchall()

    cur.close()
    conn.close()

    return rows


def debug_predictions():

    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT
            id,
            fixture_id,
            match
        FROM predictions
        ORDER BY id;
    """)

    rows = cur.fetchall()

    print("\n====== PREDICTIONS ======")

    for row in rows:
        print(row)

    cur.close()
    conn.close()    