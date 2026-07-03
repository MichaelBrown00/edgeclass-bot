from flask import Flask, request

import sqlite3

import os

import json

import hmac

import hashlib

from edgeclass_bot import run_bot



app = Flask(__name__)


def start_bot_thread():
    bot_thread = threading.Thread(target=run_bot, daemon=True)
    bot_thread.start()
start_bot_thread()

DB = "edgeclass.db"

PAYSTACK_SECRET_KEY = os.getenv("PAYSTACK_SECRET_KEY")



# ================= DATABASE =================



def update_plan(user_id, plan):

    # ADDED: timeout=20 prevents crashes when the database is busy

    conn = sqlite3.connect(DB, timeout=20)

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

    # ADDED: Security check (hmac) to ensure Paystack actually sent this

    signature = request.headers.get('x-paystack-signature')

    payload = request.data 

    

    if PAYSTACK_SECRET_KEY:

        hash_code = hmac.new(

            PAYSTACK_SECRET_KEY.encode('utf-8'),

            payload,

            digestmod=hashlib.sha512

        ).hexdigest()



        if signature != hash_code:

            return "Forbidden", 403



    try:

        data = request.get_json()

        

        # Only process successful payments

        if data.get("event") == "charge.success":

            metadata = data["data"].get("metadata", {})

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