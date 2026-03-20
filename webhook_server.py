from flask import Flask, request
import sqlite3
import os
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
DB = "edgeclass.db"

def activate_user(user_id):
    conn = sqlite3.connect(DB)
    cur = conn.cursor()

    cur.execute("""
    UPDATE users
    SET subscription='premium'
    WHERE user_id=?
    """, (user_id,))

    conn.commit()
    conn.close()


@app.route("/", methods=["GET"])
def home():
    return "Webhook Server Running"


@app.route("/webhook", methods=["POST"])
def webhook():
    data = request.json

    if data.get("event") == "charge.success":
        metadata = data["data"].get("metadata", {})
        user_id = metadata.get("telegram_user")

        if user_id:
            activate_user(user_id)

    return "OK"


if __name__ == "__main__":
    app.run(port=5000)