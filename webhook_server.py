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
    record_paystack_transaction,
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

    # --------------------------------------------------------
    # PAYSTACK SIGNATURE VERIFICATION
    # --------------------------------------------------------

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

    # --------------------------------------------------------
    # PROCESS WEBHOOK
    # --------------------------------------------------------

    try:

        data = request.get_json()

        if not data:
            print("❌ Empty Paystack webhook")
            return "Bad Request", 400

        print("EVENT:", data.get("event"))
        print("DATA:", data)

        # ----------------------------------------------------
        # SUCCESSFUL PAYMENT
        # ----------------------------------------------------

        if data.get("event") == "charge.success":

            payment_data = data.get(
                "data",
                {}
            )

            metadata = payment_data.get(
                "metadata",
                {}
            )

            print("METADATA:", metadata)

            user_id = metadata.get("user_id")
            plan = metadata.get("plan")

            reference = payment_data.get(
                "reference"
            )

            transaction_id = payment_data.get(
                "id"
            )

            amount = payment_data.get(
                "amount",
                0
            )

            currency = payment_data.get(
                "currency"
            )

            channel = payment_data.get(
                "channel"
            )

            customer = payment_data.get(
                "customer",
                {}
            )

            customer_email = customer.get(
                "email"
            )

            paid_at = payment_data.get(
                "paid_at"
            )

            print("USER:", user_id)
            print("PLAN:", plan)
            print("REFERENCE:", reference)

            # ------------------------------------------------
            # VALIDATE PAYMENT DATA
            # ------------------------------------------------

            if not user_id or not plan or not reference:

                print(
                    "❌ Missing payment metadata "
                    "or reference"
                )

                return "OK", 200

            # ------------------------------------------------
            # RECORD PAYMENT
            # ------------------------------------------------

            is_new_payment = record_paystack_transaction(
                user_id=int(user_id),
                reference=reference,
                paystack_transaction_id=transaction_id,
                amount=amount,
                currency=currency,
                plan=plan,
                status="success",
                channel=channel,
                customer_email=customer_email,
                paid_at=paid_at,
            )

            # ------------------------------------------------
            # DUPLICATE WEBHOOK PROTECTION
            # ------------------------------------------------

            if not is_new_payment:

                print(
                    "⚠️ Duplicate Paystack webhook ignored: "
                    f"{reference}"
                )

                return "OK", 200

            # ------------------------------------------------
            # UPDATE SUBSCRIPTION
            # ------------------------------------------------

            update_plan(
                int(user_id),
                plan
            )

            # ------------------------------------------------
            # REFERRAL REWARD
            # ------------------------------------------------

            reward_referrer(
                int(user_id)
            )

            apply_referral_reward(
                int(user_id)
            )

            # ------------------------------------------------
            # SUCCESS LOGGING
            # ------------------------------------------------

            print(
                "✅ Updated PostgreSQL: "
                f"{user_id} -> {plan}"
            )

            print(
                "🎁 Referral reward processed "
                f"for {user_id}"
            )

        # ----------------------------------------------------
        # OTHER PAYSTACK EVENTS
        # ----------------------------------------------------

        else:

            print(
                "ℹ️ Paystack event ignored: "
                f"{data.get('event')}"
            )

        return "OK", 200

    except Exception as e:

        print(
            "❌ WEBHOOK ERROR:",
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