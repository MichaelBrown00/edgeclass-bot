import requests
import os
from dotenv import load_dotenv

# This loads your BOT_TOKEN from your .env file automatically
load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")

# This must match your actual Render primary URL
RENDER_URL = "https://edgeclass-bot.onrender.com/telegram/webhook"

url = f"https://api.telegram.org/bot{BOT_TOKEN}/setWebhook?url={RENDER_URL}"
response = requests.get(url)
print(response.json())