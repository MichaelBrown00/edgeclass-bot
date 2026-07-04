import os
import sqlite3
import datetime
import requests
import random

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
from dotenv import load_dotenv

# ================= LOAD ENV =================
load_dotenv(override=True)

BOT_TOKEN = os.getenv("BOT_TOKEN").strip()
FOOTBALL_API_KEY = os.getenv("FOOTBALL_API_KEY").strip()
PAYSTACK_SECRET_KEY = os.getenv("PAYSTACK_SECRET_KEY").strip()

print("PAYSTACK KEY LOADED:", PAYSTACK_SECRET_KEY)

ADMIN_ID = 7634933012

PREMIUM_PRICE = 3500
VIP_PRICE = 5500

PREMIUM_CHANNEL = -1003800030990
VIP_CHANNEL = -1003732726969

DB = "edgeclass.db"

# ================= DATABASE =================

def init_db():
    conn = sqlite3.connect(DB)
    cur = conn.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS users(
        user_id INTEGER PRIMARY KEY,
        referral INTEGER,
        referrals INTEGER DEFAULT 0,
        plan TEXT DEFAULT 'free'
    )
    """)

    conn.commit()
    conn.close()


def add_user(user_id, ref=None):
    conn = sqlite3.connect(DB)
    cur = conn.cursor()

    cur.execute("SELECT * FROM users WHERE user_id=?", (user_id,))
    user = cur.fetchone()

    if not user:
        cur.execute(
            "INSERT INTO users(user_id, referral) VALUES(?,?)",
            (user_id, ref)
        )

        if ref:
            cur.execute(
                "UPDATE users SET referrals = referrals + 1 WHERE user_id=?",
                (ref,)
            )

    conn.commit()
    conn.close()


def get_referrals(user_id):
    conn = sqlite3.connect(DB)
    cur = conn.cursor()

    cur.execute("SELECT referrals FROM users WHERE user_id=?", (user_id,))
    data = cur.fetchone()

    conn.close()

    if data:
        return data[0]
    return 0


def update_plan(user_id, plan):
    conn = sqlite3.connect(DB)
    cur = conn.cursor()

    cur.execute(
        "UPDATE users SET plan=? WHERE user_id=?",
        (plan, user_id)
    )

    conn.commit()
    conn.close()


def get_plan(user_id):
    conn = sqlite3.connect(DB)
    cur = conn.cursor()

    cur.execute("SELECT plan FROM users WHERE user_id=?", (user_id,))
    data = cur.fetchone()

    conn.close()

    if data:
        return data[0]
    return "free"

# ================= FOOTBALL API =================

def ai_model():
    try:
        today = datetime.date.today().isoformat()

        url = f"https://v3.football.api-sports.io/fixtures?date={today}"
        headers = {"x-apisports-key": FOOTBALL_API_KEY}

        res = requests.get(url, headers=headers, timeout=15).json()
        fixtures = res.get("response", [])

        if not fixtures:
            return []

        bet_types = [
            "Over 1.5 Goals",
            "Over 2.5 Goals",
            "BTTS",
            "Home Win",
            "Away Win"
        ]

        bets = []

        for game in fixtures[:10]:
            home = game["teams"]["home"]["name"]
            away = game["teams"]["away"]["name"]

            confidence = random.randint(70, 90)
            bet = random.choice(bet_types)

            bets.append(
                f"{home} vs {away}\nBet: {bet}\nConfidence: {confidence}%"
            )

        return bets

    except Exception as e:
        print("AI model error:", e)
        return []

# ================= PAYSTACK =================

def create_payment(email, amount, user_id, plan):
    try:
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

        res = requests.post(url, json=data, headers=headers, timeout=15)
        response = res.json()

        if response.get("status"):
            return response["data"]["authorization_url"]
        else:
            print("Paystack error:", response)
            return None

    except Exception as e:
        print("Payment error:", e)
        return None

# ================= COMMANDS =================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user

    ref = None
    if context.args:
        ref = int(context.args[0])

    add_user(user.id, ref)

    await update.message.reply_text("""
Welcome to EdgeClass ⚽

Commands:
/edge_today
/predict
/accumulator
/pay
/upgrade_plus
/referral
/stats
/help
""")

async def edge_today(update: Update, context: ContextTypes.DEFAULT_TYPE):
    picks = ["Over 1.5", "BTTS", "Home Win"]

    match = random.choice([
        "Arsenal vs Chelsea",
        "Barcelona vs Sevilla",
        "Bayern vs Dortmund"
    ])

    pick = random.choice(picks)

    await update.message.reply_text(f"""
⚽ EDGE TODAY (FREE)

Match: {match}
Bet: {pick}

Upgrade for premium picks.
""")

async def predict(update: Update, context: ContextTypes.DEFAULT_TYPE):
    plan = get_plan(update.effective_user.id)

    if plan == "free":
        await update.message.reply_text("❌ Upgrade to Premium to access this feature.")
        return

    bets = ai_model()

    if not bets:
        await update.message.reply_text(
            "No strong edge today.\nDiscipline beats luck."
        )
        return

    msg = "🔥 EdgeClass AI Predictions\n\n"

    for b in bets[:5]:
        msg += b + "\n\n"

    await update.message.reply_text(msg)

async def accumulator(update: Update, context: ContextTypes.DEFAULT_TYPE):
    plan = get_plan(update.effective_user.id)

    if plan == "free":
        await update.message.reply_text("❌ Upgrade to Premium to access this feature.")
        return

    bets = ai_model()

    if not bets:
        await update.message.reply_text("No matches available today.")
        return

    acca = random.sample(bets, min(3, len(bets)))

    msg = "💰 Smart Accumulator\n\n"

    for b in acca:
        msg += b + "\n\n"

    msg += "Estimated Odds: 4.0+"

    await update.message.reply_text(msg)

async def pay(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    email = f"user{user.id}@gmail.com"

    link = create_payment(email, PREMIUM_PRICE, user.id, "premium")

    if not link:
        await update.message.reply_text("❌ Payment initialization failed.")
        return

    keyboard = [[InlineKeyboardButton("Pay ₦3500", url=link)]]

    await update.message.reply_text(
        "Upgrade to Premium",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def upgrade_plus(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    email = f"user{user.id}@gmail.com"

    link = create_payment(email, VIP_PRICE, user.id, "vip")

    if not link:
        await update.message.reply_text("❌ Payment initialization failed.")
        return

    keyboard = [[InlineKeyboardButton("Pay ₦5500", url=link)]]

    await update.message.reply_text(
        "Upgrade to VIP Premium+",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def referral(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    bot = await context.bot.get_me()

    link = f"https://t.me/{bot.username}?start={user.id}"

    await update.message.reply_text(f"Your referral link:\n{link}")

async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    refs = get_referrals(update.effective_user.id)

    await update.message.reply_text(f"You have {refs} referrals.")

async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("""
EdgeClass Commands

/start
/edge_today
/predict
/accumulator
/pay
/upgrade_plus
/referral
/stats
/help
""")

# ================= MAIN =================
async def process_telegram_update(update_dict):
    # This function allows Flask to feed updates into the bot
    from telegram import Update
    update = Update.de_json(update_dict, application.bot)
    await application.process_update(update)

def init_bot():
    global application
    init_db()
    from telegram.ext import Application
    application = ApplicationBuilder().token(BOT_TOKEN).build()

    # Add your handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("edge_today", edge_today))
    application.add_handler(CommandHandler("predict", predict))
    application.add_handler(CommandHandler("accumulator", accumulator))
    application.add_handler(CommandHandler("pay", pay))
    application.add_handler(CommandHandler("upgrade_plus", upgrade_plus))
    application.add_handler(CommandHandler("referral", referral))
    application.add_handler(CommandHandler("stats", stats))
    application.add_handler(CommandHandler("help", help_cmd))

    return application

async def process_telegram_update(update_dict):
    from telegram import Update
    update = Update.de_json(update_dict, application.bot)
    await application.process_update(update)

print("EdgeClass Bot Initialized.")
