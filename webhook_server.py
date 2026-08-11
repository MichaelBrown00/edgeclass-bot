import os
import hmac
import hashlib
import asyncio

from flask import Flask, request

from edgeclass_bot import (
    process_telegram_update,
    start_telegram,
)

from database import (
    update_plan,
    reward_referrer,
    apply_referral_reward,
)

from config import PAYSTACK_SECRET_KEY

app = Flask(__name__)


# ============================================================
# START TELEGRAM BACKGROUND WORKER
# ============================================================

start_telegram()

print("🔥 Telegram background worker started")


@app.route("/")
def home():
    return "Webhook Server Running"


# ---------------- TELEGRAM WEBHOOK ----------------

@app.route("/telegram/webhook", methods=["POST"])
def telegram_webhook():
    update = request.get_json()

    print("📩 TELEGRAM WEBHOOK RECEIVED")

    try:
        asyncio.run(
            process_telegram_update(update)
        )

        print("✅ TELEGRAM UPDATE PROCESSED")

        return "OK", 200

    except Exception as e:
        print("❌ TELEGRAM WEBHOOK ERROR:", repr(e))

        return "Error", 500

# ---------------- PAYSTACK WEBHOOK ----------------

@app.route("/paystack/webhook", methods=["POST"])
def paystack_webhook():

    print("========== PAYSTACK WEBHOOK HIT ==========")

    signature = request.headers.get("x-paystack-signature")
    payload = request.data

    if PAYSTACK_SECRET_KEY:
        hash_code = hmac.new(
            PAYSTACK_SECRET_KEY.encode(),
            payload,
            hashlib.sha512
        ).hexdigest()

        if signature != hash_code:
            print("❌ Invalid signature")
            return "Forbidden", 403

    try:
        data = request.get_json()

        print("EVENT:", data.get("event"))
        print("DATA:", data)

        if data.get("event") == "charge.success":

            metadata = data["data"].get("metadata", {})

            print("METADATA:", metadata)

            user_id = metadata.get("user_id")
            plan = metadata.get("plan")

            print("USER:", user_id)
            print("PLAN:", plan)

            if user_id and plan:

                update_plan(int(user_id), plan)

                reward_referrer(int(user_id))

                apply_referral_reward(int(user_id))

                print(f"✅ Updated PostgreSQL: {user_id} -> {plan}")
                print(f"🎉 Referral reward processed for {user_id}")

            else:
                print("❌ Missing metadata")

        return "OK", 200

    except Exception as e:
        print("WEBHOOK ERROR:", e)
        return "Error", 500


if __name__ == "__main__":
    app.run(
        host="127.0.0.1",
        port=10000,
        debug=False,
    )