import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv(override=True)

# Telegram
BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID", "0"))

# APIs
FOOTBALL_API_KEY = os.getenv("FOOTBALL_API_KEY")
FOOTBALL_DATA_KEY = os.getenv("FOOTBALL_DATA_KEY")
PAYSTACK_SECRET_KEY = os.getenv("PAYSTACK_SECRET_KEY")

# Database
DATABASE_URL = os.getenv("DATABASE_URL")

# Pricing
PREMIUM_PRICE = 3500
VIP_PRICE = 5500

# Telegram Channels
PREMIUM_CHANNEL = -1003800030990
VIP_CHANNEL = -1003732726969

#Admin Panel
OWNER_ID = 8430501696

SUPER_ADMIN_IDS = [
    7634933012,
]

PREMIUM_MODERATOR_IDS = [
    7888002834,
]