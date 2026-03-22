from flask import Flask, request, jsonify

app = Flask(__name__)

@app.route("/")
def home():
    return "Webhook Server Running"

@app.route("/paystack/webhook", methods=["POST"])
def paystack_webhook():
    data = request.json
    print("Webhook received:", data)

    # TEMP response (we will upgrade later)
    return jsonify({"status": "success"}), 200


if __name__ == "__main__":
    import os
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)