import os
import hmac
import hashlib
import asyncio
import threading
import time

from flask import Flask, request

from edgeclass_bot import (
    process_telegram_update,
    start_telegram,
    telegram_ready,
)

from database import (
    update_plan,
    reward_referrer,
    apply_referral_reward,
)

from config import PAYSTACK_SECRET_KEY


app = Flask(__name__)

telegram_started = False
telegram_start_lock = threading.Lock()


def ensure_telegram_started():
    global telegram_started

    if telegram_started:
        return

    with telegram_start_lock:
        if telegram_started:
            return

        print("🔥 Starting Telegram worker...")

        start_telegram()

        # Give the background thread time to initialize PTB.
        for _ in range(60):
            if telegram_ready.is_set():
                telegram_started = True
                print("🔥 Telegram worker is READY")
                return

            time.sleep(0.5)

        raise RuntimeError(
            "Telegram application failed to become ready."
        )


@app.route("/")
def home():
    return "Webhook Server Running"


@app.route("/telegram/webhook", methods=["POST"])
def telegram_webhook():

    print("📩 TELEGRAM WEBHOOK RECEIVED")

    try:
        ensure_telegram_started()

        update = request.get_json()

        if not update:
            print("❌ Empty Telegram update")
            return "Bad Request", 400

        asyncio.run(
            process_telegram_update(update)
        )

        print("✅ TELEGRAM UPDATE PROCESSED")

        return "OK", 200

    except Exception as e:
        print(
            "❌ TELEGRAM WEBHOOK ERROR:",
            repr(e)
        )

        return "Error", 500


@app.route("/paystack/webhook", methods=["POST"])
def paystack_webhook():

    print("========== PAYSTACK WEBHOOK HIT ==========")

    signature = request.headers.get(
        "x-paystack-signature"
    )

    payload = request.data

    if PAYSTACK_SECRET_KEY:

        hash_code = hmac.new(
            PAYSTACK_SECRET_KEY.encode(),
            payload,
            hashlib.sha512
        ).hexdigest()

        if not hmac.compare_digest(
            signature or "",
            hash_code
        ):
            print("❌ Invalid signature")
            return "Forbidden", 403

    try:

        data = request.get_json()

        print("EVENT:", data.get("event"))
        print("DATA:", data)

        if data.get("event") == "charge.success":

            metadata = data["data"].get(
                "metadata",
                {}
            )

            print("METADATA:", metadata)

            user_id = metadata.get("user_id")
            plan = metadata.get("plan")

            print("USER:", user_id)
            print("PLAN:", plan)

            if user_id and plan:

                update_plan(
                    int(user_id),
                    plan
                )

                reward_referrer(
                    int(user_id)
                )

                apply_referral_reward(
                    int(user_id)
                )

                print(
                    f"✅ Updated PostgreSQL: "
                    f"{user_id} -> {plan}"
                )

                print(
                    f"🎁 Referral reward processed "
                    f"for {user_id}"
                )

            else:
                print("❌ Missing metadata")

        return "OK", 200

    except Exception as e:

        print(
            "WEBHOOK ERROR:",
            repr(e)
        )

        return "Error", 500


if __name__ == "__main__":

    ensure_telegram_started()

    app.run(
        host="127.0.0.1",
        port=10000,
        debug=False,
    )