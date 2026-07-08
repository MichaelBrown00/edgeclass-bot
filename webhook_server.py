import os
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

                print(f"✅ Updated PostgreSQL: {user_id} -> {plan}")
            else:
                print("❌ Missing metadata")

        return "OK", 200

    except Exception as e:
        print("WEBHOOK ERROR:", e)
        return "Error", 500



if __name__ == "__main__":

    port = int(os.environ.get("PORT", 5000))

    app.run(host="0.0.0.0", port=port)