import requests
from config import PAYSTACK_SECRET_KEY


def create_payment(email, amount, user_id, plan):
    """
    Creates a Paystack payment link.
    """

    url = "https://api.paystack.co/transaction/initialize"

    headers = {
        "Authorization": f"Bearer {PAYSTACK_SECRET_KEY}",
        "Content-Type": "application/json"
    }

    data = {
        "email": email,
        "amount": amount * 100,
        "metadata": {
            "user_id": user_id,
            "plan": plan
        }
    }

    try:
        response = requests.post(
            url,
            json=data,
            headers=headers,
            timeout=20
        )

        result = response.json()

        if result.get("status"):
            return result["data"]["authorization_url"]

        print("Paystack Error:", result)
        return None

    except Exception as e:
        print("Payment Error:", e)
        return None