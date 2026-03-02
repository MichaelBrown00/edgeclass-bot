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
    main()