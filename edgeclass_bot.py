import random

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    ContextTypes,
)

from config import (
    BOT_TOKEN,
    PREMIUM_PRICE,
    VIP_PRICE,
)

from database import (
    add_user,
    get_referrals,
    get_plan,
)

from payments import create_payment
from football_api import ai_model


from database import init_db

init_db()


# ================= COMMANDS =================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user

    ref = None
    if context.args:
        try:
            ref = int(context.args[0])
        except ValueError:
            ref = None

    add_user(user.id, ref)

    await update.message.reply_text(
        """
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
"""
    )


async def edge_today(update: Update, context: ContextTypes.DEFAULT_TYPE):
    picks = [
        "Over 1.5",
        "BTTS",
        "Home Win",
    ]

    matches = [
        "Arsenal vs Chelsea",
        "Barcelona vs Sevilla",
        "Bayern vs Dortmund",
    ]

    await update.message.reply_text(
        f"""
⚽ EDGE TODAY (FREE)

Match: {random.choice(matches)}
Bet: {random.choice(picks)}

Upgrade for Premium predictions.
"""
    )


async def predict(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if get_plan(update.effective_user.id) == "free":
        await update.message.reply_text(
            "❌ Upgrade to Premium to use this feature."
        )
        return

    bets = ai_model()

    if not bets:
        await update.message.reply_text(
            "No strong edge today."
        )
        return

    message = "🔥 EdgeClass AI Predictions\n\n"

    for bet in bets[:5]:
        message += bet + "\n\n"

    await update.message.reply_text(message)


async def accumulator(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if get_plan(update.effective_user.id) == "free":
        await update.message.reply_text(
            "❌ Upgrade to Premium."
        )
        return

    bets = ai_model()

    if not bets:
        await update.message.reply_text(
            "No matches today."
        )
        return

    selected = random.sample(
        bets,
        min(3, len(bets))
    )

    msg = "💰 Smart Accumulator\n\n"

    for bet in selected:
        msg += bet + "\n\n"

    msg += "Estimated Odds: 4.0+"

    await update.message.reply_text(msg)


async def pay(update: Update, context: ContextTypes.DEFAULT_TYPE):

    user = update.effective_user

    email = f"user{user.id}@gmail.com"

    url = create_payment(
        email=email,
        amount=PREMIUM_PRICE,
        user_id=user.id,
        plan="premium",
    )

    if not url:
        await update.message.reply_text(
            "Payment initialization failed."
        )
        return

    keyboard = [
        [
            InlineKeyboardButton(
                "Pay ₦3500",
                url=url,
            )
        ]
    ]

    await update.message.reply_text(
        "Upgrade to Premium",
        reply_markup=InlineKeyboardMarkup(keyboard),
    )


async def upgrade_plus(update: Update, context: ContextTypes.DEFAULT_TYPE):

    user = update.effective_user

    email = f"user{user.id}@gmail.com"

    url = create_payment(
        email=email,
        amount=VIP_PRICE,
        user_id=user.id,
        plan="vip",
    )

    if not url:
        await update.message.reply_text(
            "Payment initialization failed."
        )
        return

    keyboard = [
        [
            InlineKeyboardButton(
                "Pay ₦5500",
                url=url,
            )
        ]
    ]

    await update.message.reply_text(
        "Upgrade to VIP",
        reply_markup=InlineKeyboardMarkup(keyboard),
    )


async def referral(update: Update, context: ContextTypes.DEFAULT_TYPE):

    bot = await context.bot.get_me()

    link = (
        f"https://t.me/{bot.username}"
        f"?start={update.effective_user.id}"
    )

    await update.message.reply_text(
        f"Referral Link:\n{link}"
    )


async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE):

    refs = get_referrals(update.effective_user.id)

    await update.message.reply_text(
        f"You have {refs} referrals."
    )


async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):

    await update.message.reply_text(
        """
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
"""
    )


# ================= APPLICATION =================

application = ApplicationBuilder().token(BOT_TOKEN).build()

application.add_handler(CommandHandler("start", start))
application.add_handler(CommandHandler("edge_today", edge_today))
application.add_handler(CommandHandler("predict", predict))
application.add_handler(CommandHandler("accumulator", accumulator))
application.add_handler(CommandHandler("pay", pay))
application.add_handler(CommandHandler("upgrade_plus", upgrade_plus))
application.add_handler(CommandHandler("referral", referral))
application.add_handler(CommandHandler("stats", stats))
application.add_handler(CommandHandler("help", help_cmd))


initialized = False


async def process_telegram_update(update_dict):
    global initialized

    if not initialized:
        await application.initialize()
        initialized = True

    update = Update.de_json(update_dict, application.bot)
    await application.process_update(update)