<<<<<<< HEAD
import os
import sqlite3
import requests
import time

from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    ContextTypes,
)

# =========================
# ENVIRONMENT VARIABLES
# =========================
BOT_TOKEN = os.getenv("BOT_TOKEN")
PAYSTACK_SECRET_KEY = os.getenv("PAYSTACK_SECRET_KEY")

# =========================
# CONFIG
# =========================
ADMIN_ID = 123456789  # ← REPLACE with your Telegram ID
PREMIUM_GROUP_ID = -1001234567890  # ← REPLACE with Premium group ID
VIP_GROUP_ID = -1003732726969      # ✅ YOUR Premium+ VIP GROUP

PREMIUM_AMOUNT = 350000        # ₦3,500
PREMIUM_PLUS_AMOUNT = 800000   # ₦8,000

SECONDS_30_DAYS = 30 * 24 * 60 * 60

# =========================
# DATABASE
# =========================
conn = sqlite3.connect("users.db", check_same_thread=False)
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    telegram_id INTEGER PRIMARY KEY,
    is_premium INTEGER DEFAULT 0,
    premium_until INTEGER DEFAULT 0,
    tier TEXT DEFAULT 'free'
)
""")
conn.commit()

# =========================
# DATABASE HELPERS
# =========================
def get_user(user_id: int):
    cursor.execute(
        "SELECT premium_until, tier FROM users WHERE telegram_id = ?",
        (user_id,)
    )
    return cursor.fetchone()

def premium_days_left(user_id: int) -> int:
    row = get_user(user_id)
    if not row:
        return 0
    return max(0, int((row[0] - time.time()) / 86400))

def is_premium(user_id: int) -> bool:
    row = get_user(user_id)
    return row is not None and row[0] > time.time()

def get_tier(user_id: int) -> str:
    row = get_user(user_id)
    return row[1] if row else "free"

def grant_premium(user_id: int, tier: str):
    now = int(time.time())
    row = get_user(user_id)

    if row and row[0] > now:
        expiry = row[0] + SECONDS_30_DAYS
    else:
        expiry = now + SECONDS_30_DAYS

    cursor.execute("""
        INSERT OR REPLACE INTO users
        (telegram_id, is_premium, premium_until, tier)
        VALUES (?, 1, ?, ?)
    """, (user_id, expiry, tier))
    conn.commit()

# =========================
# PAYMENT TRACKING
# =========================
pending_payments = {}  # reference -> (tier, user_id)

# =========================
# BACKGROUND JOBS
# =========================
async def auto_verify_payments(context: ContextTypes.DEFAULT_TYPE):
    app = context.application

    for reference, (tier, user_id) in list(pending_payments.items()):
        try:
            headers = {
                "Authorization": f"Bearer {PAYSTACK_SECRET_KEY}"
            }
            r = requests.get(
                f"https://api.paystack.co/transaction/verify/{reference}",
                headers=headers,
                timeout=10
            )
            data = r.json()

            if data.get("status") and data["data"]["status"] == "success":
                grant_premium(user_id, tier)

                if tier == "premium_plus":
                    await invite_to_vip_group(user_id, app)
                    msg = "💠 Premium+ activated for 30 days!"
                else:
                    await invite_to_premium_group(user_id, app)
                    msg = "💎 Premium activated for 30 days!"

                await app.bot.send_message(user_id, msg)
                del pending_payments[reference]

        except Exception as e:
            print("Payment verify error:", e)

async def expire_premiums(context: ContextTypes.DEFAULT_TYPE):
    now = int(time.time())
    cursor.execute("""
        UPDATE users
        SET is_premium = 0, tier = 'free'
        WHERE premium_until < ?
    """, (now,))
    conn.commit()

# =========================
# GROUP INVITES
# =========================
async def invite_to_premium_group(user_id: int, app):
    try:
        await app.bot.get_chat_member(PREMIUM_GROUP_ID, user_id)
    except:
        link = await app.bot.create_chat_invite_link(
            PREMIUM_GROUP_ID,
            member_limit=1
        )
        await app.bot.send_message(
            user_id,
            f"💎 Join Premium Group:\n{link.invite_link}"
        )

async def invite_to_vip_group(user_id: int, app):
    try:
        await app.bot.get_chat_member(VIP_GROUP_ID, user_id)
    except:
        link = await app.bot.create_chat_invite_link(
            VIP_GROUP_ID,
            member_limit=1
        )
        await app.bot.send_message(
            user_id,
            f"💠 Welcome to Premium+\nJoin VIP Group:\n{link.invite_link}"
        )

# =========================
# COMMANDS
# =========================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 Welcome to EdgeClass Football Bot\n\n"
        "/edge_today – Free analysis\n"
        "/premium_edge – Premium analysis\n"
        "/premium_plus – Premium+ analysis\n"
        "/pay – Buy Premium\n"
        "/upgrade_plus – Upgrade to Premium+"
    )

async def edge_today(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "⚽ EDGE TODAY (FREE)\n\nNo strong edge today."
    )

async def premium_edge(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id

    if not is_premium(user_id):
        await update.message.reply_text("🔒 Premium only. Use /pay.")
        return

    days = premium_days_left(user_id)
    await update.message.reply_text(
        f"💎 PREMIUM EDGE\n\n⏳ {days} days remaining."
    )

async def premium_plus(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id

    if get_tier(user_id) != "premium_plus":
        await update.message.reply_text("🔒 Premium+ only. Use /upgrade_plus.")
        return

    days = premium_days_left(user_id)
    await update.message.reply_text(
        f"💠 PREMIUM+\n\nElite edge active.\n⏳ {days} days left."
    )

# =========================
# PAY COMMANDS
# =========================
async def pay(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    reference = f"premium-{user_id}-{int(time.time())}"

    headers = {
        "Authorization": f"Bearer {PAYSTACK_SECRET_KEY}",
        "Content-Type": "application/json"
    }

    payload = {
        "email": f"{user_id}@edgeclass.app",
        "amount": PREMIUM_AMOUNT,
        "reference": reference
    }

    r = requests.post(
        "https://api.paystack.co/transaction/initialize",
        json=payload,
        headers=headers,
        timeout=10
    )

    data = r.json()

    if data.get("status"):
        pending_payments[reference] = ("premium", user_id)
        await update.message.reply_text(
            f"💳 Pay to unlock Premium:\n{data['data']['authorization_url']}"
        )
    else:
        await update.message.reply_text("❌ Payment failed.")

async def upgrade_plus(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    reference = f"plus-{user_id}-{int(time.time())}"

    headers = {
        "Authorization": f"Bearer {PAYSTACK_SECRET_KEY}",
        "Content-Type": "application/json"
    }

    payload = {
        "email": f"{user_id}@edgeclass.app",
        "amount": PREMIUM_PLUS_AMOUNT,
        "reference": reference
    }

    r = requests.post(
        "https://api.paystack.co/transaction/initialize",
        json=payload,
        headers=headers,
        timeout=10
    )

    data = r.json()

    if data.get("status"):
        pending_payments[reference] = ("premium_plus", user_id)
        await update.message.reply_text(
            f"💠 Upgrade to Premium+:\n{data['data']['authorization_url']}"
        )
    else:
        await update.message.reply_text("❌ Payment failed.")

# =========================
# ADMIN
# =========================
async def give_premium(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.from_user.id != ADMIN_ID:
        await update.message.reply_text("❌ Not authorized.")
        return

    if len(context.args) != 2:
        await update.message.reply_text(
            "Usage: /give_premium USER_ID premium|premium_plus"
        )
        return

    target = int(context.args[0])
    tier = context.args[1]

    if tier not in ("premium", "premium_plus"):
        await update.message.reply_text("Invalid tier.")
        return

    grant_premium(target, tier)
    await update.message.reply_text("✅ Granted successfully.")

# =========================
# MAIN
# =========================
def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("edge_today", edge_today))
    app.add_handler(CommandHandler("premium_edge", premium_edge))
    app.add_handler(CommandHandler("premium_plus", premium_plus))
    app.add_handler(CommandHandler("pay", pay))
    app.add_handler(CommandHandler("upgrade_plus", upgrade_plus))
    app.add_handler(CommandHandler("give_premium", give_premium))

    app.job_queue.run_repeating(auto_verify_payments, interval=10, first=10)
    app.job_queue.run_repeating(expire_premiums, interval=3600, first=60)

    print("✅ Bot is running...")
    app.run_polling()

if __name__ == "__main__":
=======
import sqlite3
import requests
import time

from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    ContextTypes,
)

# =========================
# CONFIG — EDIT THESE
# =========================
import os

BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = 7634933012            # 👈 YOUR Telegram numeric ID (NO quotes)
PREMIUM_GROUP_ID = -1003800030990  # 👈 Your supergroup ID (NO quotes)

# PAYSTACK
PAYSTACK_SECRET_KEY = os.getenv("PAYSTACK_SECRET_KEY")
PAYMENT_AMOUNT = 350000  # ₦3,500 (Paystack uses kobo)"

# =========================
# DATABASE (SQLite)
# =========================
conn = sqlite3.connect("users.db", check_same_thread=False)
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    telegram_id INTEGER PRIMARY KEY,
    is_premium INTEGER DEFAULT 0,
    premium_until INTEGER DEFAULT 0
)
""")
conn.commit()

# =========================
# TIME CONSTANTS
# =========================
SECONDS_30_DAYS = 30 * 24 * 60 * 60

# =========================
# DATABASE HELPERS
# =========================
def grant_premium(user_id: int):
    now = int(time.time())

    cursor.execute(
        "SELECT premium_until FROM users WHERE telegram_id = ?",
        (user_id,)
    )
    row = cursor.fetchone()

    if row and row[0] > now:
        new_expiry = row[0] + SECONDS_30_DAYS
    else:
        new_expiry = now + SECONDS_30_DAYS

    cursor.execute("""
        INSERT OR REPLACE INTO users (telegram_id, is_premium, premium_until)
        VALUES (?, 1, ?)
    """, (user_id, new_expiry))
    conn.commit()


def is_premium(user_id: int) -> bool:
    now = int(time.time())
    cursor.execute(
        "SELECT premium_until FROM users WHERE telegram_id = ?",
        (user_id,)
    )
    row = cursor.fetchone()
    return row is not None and row[0] > now


def premium_days_left(user_id: int) -> int:
    cursor.execute(
        "SELECT premium_until FROM users WHERE telegram_id = ?",
        (user_id,)
    )
    row = cursor.fetchone()
    if not row:
        return 0
    return max(0, int((row[0] - time.time()) / 86400))

# =========================
# PAYMENT TRACKING
# =========================
pending_payments = {}  # reference -> user_id

# =========================
# BACKGROUND JOB (EXPIRY + VERIFY)
# =========================
async def auto_verify_payments(context: ContextTypes.DEFAULT_TYPE):
    app = context.application

    for reference, user_id in list(pending_payments.items()):
        try:
            headers = {
                "Authorization": f"Bearer {PAYSTACK_SECRET_KEY}"
            }
            r = requests.get(
                f"https://api.paystack.co/transaction/verify/{reference}",
                headers=headers,
                timeout=10
            )
            data = r.json()

            if data.get("status") and data["data"]["status"] == "success":
                grant_premium(user_id)
                await invite_to_premium_group(user_id, app)
                await app.bot.send_message(
                    user_id,
                    "✅ Payment successful!\n💎 Premium activated for 30 days."
                )
                del pending_payments[reference]

        except Exception as e:
            print("Paystack error:", e)


async def expire_premiums(context: ContextTypes.DEFAULT_TYPE):
    now = int(time.time())
    cursor.execute("""
        UPDATE users
        SET is_premium = 0
        WHERE premium_until < ?
    """, (now,))
    conn.commit()

# =========================
# BOT COMMANDS
# =========================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 Welcome to EdgeClass Football Bot\n\n"
        "Commands:\n"
        "/edge_today – Free analysis\n"
        "/premium_edge – Premium analysis\n"
        "/pay – Upgrade to Premium"
    )

async def edge_today(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "⚽ EDGE TODAY (FREE)\n\n"
        "No strong edge detected today.\n"
        "Education first. Discipline wins."
    )

async def premium_edge(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id

    if not is_premium(user_id):
        await update.message.reply_text(
            "🔒 Premium only.\nUse /pay to upgrade."
        )
        return

    days = premium_days_left(user_id)
    await update.message.reply_text(
        f"💎 PREMIUM EDGE\n\n"
        f"Advanced market insight.\n"
        f"⏳ {days} days remaining."
    )

# =========================
# PAY COMMAND
# =========================
async def pay(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    reference = f"{user_id}-{int(time.time())}"

    headers = {
        "Authorization": f"Bearer {PAYSTACK_SECRET_KEY}",
        "Content-Type": "application/json"
    }

    payload = {
        "email": f"{user_id}@edgeclass.app",
        "amount": PAYMENT_AMOUNT,
        "reference": reference
    }

    r = requests.post(
        "https://api.paystack.co/transaction/initialize",
        json=payload,
        headers=headers,
        timeout=10
    )

    data = r.json()

    if data.get("status"):
        pending_payments[reference] = user_id
        await update.message.reply_text(
            f"💳 Pay here to unlock Premium:\n{data['data']['authorization_url']}"
        )
    else:
        await update.message.reply_text("❌ Payment failed. Try again.")

# =========================
# ADMIN COMMAND
# =========================
async def give_premium(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.from_user.id != ADMIN_ID:
        await update.message.reply_text("❌ Not authorized.")
        return

    if not context.args:
        await update.message.reply_text("Usage: /give_premium USER_ID")
        return

    target = int(context.args[0])
    grant_premium(target)
    await invite_to_premium_group(target, context.application)
    await update.message.reply_text("✅ Premium granted for 30 days.")

# =========================
# GROUP INVITE
# =========================
async def invite_to_premium_group(user_id: int, app):
    try:
        await app.bot.get_chat_member(PREMIUM_GROUP_ID, user_id)
    except:
        link = await app.bot.create_chat_invite_link(
            PREMIUM_GROUP_ID,
            member_limit=1
        )
        await app.bot.send_message(
            user_id,
            f"💎 Join Premium Group:\n{link.invite_link}"
        )

# =========================
# MAIN
# =========================
def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("edge_today", edge_today))
    app.add_handler(CommandHandler("premium_edge", premium_edge))
    app.add_handler(CommandHandler("pay", pay))
    app.add_handler(CommandHandler("give_premium", give_premium))

    app.job_queue.run_repeating(auto_verify_payments, interval=10, first=10)
    app.job_queue.run_repeating(expire_premiums, interval=3600, first=60)

    print("✅ Bot is running...")
    app.run_polling()

if __name__ == "__main__":
>>>>>>> d80563c9a9631c1489144fc4f50845b2d0a78c98
    main()