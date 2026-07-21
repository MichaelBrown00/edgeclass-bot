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
    get_successful_referrals,
    get_plan,
    get_user,
    expire_user,
    check_subscription,
    save_prediction,
    get_prediction_history,
)

from payments import create_payment
from football_api import ai_model


from database import init_db


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
/myplan
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

    if check_subscription(update.effective_user.id) == "free":
        await update.message.reply_text(
            "❌ Upgrade to Premium to use this feature."
        )
        return

    bets = ai_model()

    for bet in bets:
        print(bet)

    if not bets:
        await update.message.reply_text(
            "⚠️ No strong edge found today."
        )
        return

    message = "🔥 EdgeClass AI Predictions\n\n"

    for bet in bets[:5]:

        save_prediction(
            bet["fixture_id"],
            bet["match"],
            bet["prediction"],
            bet["confidence"],
            bet["odds"],
            bet["league"],
            bet["kickoff"]
        )

        message += (
            f"⚽ {bet['match']}\n"
            f"🏆 {bet['league']}\n"
            f"🎯 Bet: {bet['prediction']}\n"
            f"📈 Confidence: {bet['confidence']}%\n"
            f"💰 Odds: {bet['odds']}\n\n"
        )

        bets = ai_model()

        print(bets)

    await update.message.reply_text(message)


async def accumulator(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if check_subscription(update.effective_user.id) == "free":
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
    successful = get_successful_referrals(update.effective_user.id)

    if successful >= 20:
        reward = "🏆 Founder VIP Badge"
        next_reward = "You've unlocked every reward!"
    elif successful >= 10:
        reward = "💎 Lifetime Premium"
        next_reward = "10 more referrals → Founder VIP Badge"
    elif successful >= 5:
        reward = "👑 30 Days VIP"
        next_reward = "5 more referrals → Lifetime Premium"
    elif successful >= 3:
        reward = "⭐ 7 Days Premium"
        next_reward = "2 more referrals → 30 Days VIP"
    elif successful >= 1:
        reward = "🎯 Free Premium Prediction"
        next_reward = "2 more referrals → 7 Days Premium"
    else:
        reward = "None yet"
        next_reward = "1 referral → Free Premium Prediction"

    message = f"""
📊 EdgeClass Referral Stats

👥 Total Referrals:
{refs}

💎 Successful Referrals:
{successful}

🏆 Current Reward:
{reward}

🎁 Next Reward:
{next_reward}
"""

    await update.message.reply_text(message)


async def myplan(update: Update, context: ContextTypes.DEFAULT_TYPE):

    user = get_user(update.effective_user.id)

    if not user:

        await update.message.reply_text(
            "No account found."
        )
        return

    plan, joined, expiry = user

    if not joined:
        joined = "Not available"

    if not expiry:
        expiry = "Unlimited"

    emoji = "🆓"

    if plan == "premium":
        emoji = "⭐"

    elif plan == "vip":
        emoji = "👑"

    message = f"""
👤 Your EdgeClass Account

Plan:
{emoji} {plan.upper()}

Joined:
{joined}

Expires:
{expiry}
"""

    await update.message.reply_text(message)


async def expireme(update: Update, context: ContextTypes.DEFAULT_TYPE):

    # Only you can use this command
    if update.effective_user.id != 8519398783:
        await update.message.reply_text("❌ Unauthorized.")
        return

    expire_user(update.effective_user.id)

    await update.message.reply_text(
        "✅ Your Premium subscription has been expired for testing."
    )


async def history(update: Update, context: ContextTypes.DEFAULT_TYPE):

    rows = get_prediction_history()

    if not rows:

        await update.message.reply_text(
            "No prediction history yet."
        )

        return

    message = "📈 EdgeClass Prediction History\n\n"

    for row in rows:

        (
            match,
            prediction,
            confidence,
            odds,
            league,
            kickoff,
            status,
            actual_score
        ) = row

        message += (
            "━━━━━━━━━━━━━━━━━━\n\n"

            f"⚽ {match}\n\n"

            f"🏆 {league}\n"
            f"🕒 Kickoff: {kickoff}\n\n"

            f"🎯 Prediction\n"
            f"{prediction}\n\n"

            f"📈 Confidence\n"
            f"{confidence}%\n\n"

            f"💰 Odds\n"
            f"{odds}\n\n"
        )

        if status == "Pending":

            message += "⏳ Awaiting Result\n\n"

        else:

            message += (
                f"⚽ Final Score\n"
                f"{actual_score}\n\n"

                f"✅ RESULT\n"
                f"{status}\n\n"
            )

    await update.message.reply_text(message)


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
/myplan
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
application.add_handler(CommandHandler("myplan", myplan))
application.add_handler(CommandHandler("admin_expire", expireme))
application.add_handler(CommandHandler("history", history))
application.add_handler(CommandHandler("help", help_cmd))


async def process_telegram_update(update_dict):
    await application.initialize()

    try:
        update = Update.de_json(update_dict, application.bot)
        await application.process_update(update)
    finally:
        await application.shutdown()