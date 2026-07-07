import os
import sqlite3
import hmac
import hashlib
import asyncio

from flask import Flask, request

from edgeclass_bot import process_telegram_update
from database import update_plan
from config import PAYSTACK_SECRET_KEY

app = Flask(__name__)


@app.route("/")
def home():
    return "Webhook Server Running"


# ---------------- TELEGRAM WEBHOOK ----------------

@app.route("/telegram/webhook", methods=["POST"])
def telegram_webhook():
    update = request.get_json()

    asyncio.run(process_telegram_update(update))

    return "OK", 200

@app.route("/db")
def db():
    import sqlite3
    from config import DB

    conn = sqlite3.connect(DB)
    cur = conn.cursor()

    cur.execute("PRAGMA table_info(users)")
    rows = cur.fetchall()

    conn.close()

    return str(rows)

@app.route("/debug/user/<int:user_id>")
def debug_user(user_id):
    import sqlite3
    from config import DB

    conn = sqlite3.connect(DB)
    cur = conn.cursor()

    cur.execute("PRAGMA table_info(users)")
    schema = cur.fetchall()

    cur.execute(
        "SELECT * FROM users WHERE user_id=?",
        (user_id,)
    )
    user = cur.fetchone()

    conn.close()

    return {
        "schema": schema,
        "user": user,
    }


# ---------------- PAYSTACK WEBHOOK ----------------

@app.route("/paystack/webhook", methods=["POST"])
def paystack_webhook():

    signature = request.headers.get("x-paystack-signature")
    payload = request.data

    if PAYSTACK_SECRET_KEY:

        hash_code = hmac.new(
            PAYSTACK_SECRET_KEY.encode(),
            payload,
            hashlib.sha512
        ).hexdigest()

        if signature != hash_code:
            return "Forbidden", 403

    try:

        data = request.get_json()

        if data["event"] == "charge.success":

            metadata = data["data"]["metadata"]

            user_id = metadata["user_id"]
            plan = metadata["plan"]

            update_plan(user_id, plan)

            print(f"✅ User {user_id} upgraded to {plan}")

        return "OK", 200

    except Exception as e:

        print(e)

        return "Error", 500


if __name__ == "__main__":

    port = int(os.environ.get("PORT", 5000))

    app.run(host="0.0.0.0", port=port)