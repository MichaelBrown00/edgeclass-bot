from flask import Flask, request
import sqlite3
import os
import json

app = Flask(__name__)

DB = "edgeclass.db"

# ================= DATABASE =================

def update_plan(user_id, plan):
    conn = sqlite3.connect(DB)
    cur = conn.cursor()

    cur.execute(
        "UPDATE users SET plan=? WHERE user_id=?",
        (plan, user_id)
    )

    conn.commit()
    conn.close()


# ================= ROUTES =================

@app.route("/")
def home():
    return "Webhook Server Running"


@app.route("/paystack/webhook", methods=["POST"])
def paystack_webhook():
    try:
        data = request.get_json()

        print("FULL WEBHOOK DATA:")
        print(json.dumps(data, indent=2))

        # Only process successful payments
        if data["event"] == "charge.success":

            metadata = data["data"]["metadata"]

            user_id = metadata.get("user_id")
            plan = metadata.get("plan")

            if user_id and plan:
                update_plan(user_id, plan)
                print(f"✅ User {user_id} upgraded to {plan}")
            else:
                print("❌ Missing metadata")

        return "OK", 200

    except Exception as e:
        print("Webhook error:", e)
        return "Error", 500


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)