import requests

from config import PAYSTACK_SECRET_KEY
from database import update_plan

REFERENCE = "T543331377961389"

headers = {
    "Authorization": f"Bearer {PAYSTACK_SECRET_KEY}"
}

url = f"https://api.paystack.co/transaction/verify/{REFERENCE}"

response = requests.get(url, headers=headers)
data = response.json()

print(data)

if data["status"] and data["data"]["status"] == "success":

    metadata = data["data"]["metadata"]

    user_id = metadata["user_id"]
    plan = metadata["plan"]

    update_plan(user_id, plan)

    print(f"✅ User {user_id} upgraded to {plan}")

else:
    print("❌ Payment verification failed.")