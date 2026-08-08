import random

from analytics import get_prediction_stats
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CallbackQueryHandler
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

from permissions import (
    is_owner,
    is_super_admin,
    is_premium_moderator
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
    remove_duplicate_predictions,
)

from admin_panel import (
    admin,
    admin_callback,
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
🏆 Welcome to EdgeClass AI

The intelligent football prediction platform powered by advanced AI analysis.

🔥 What you can do:

⚽ /edge_today
Today's free AI prediction.

🤖 /predict
Generate premium AI match predictions.

🎯 /accumulator
Receive a smart accumulator ticket.

💎 /pay
Upgrade to Premium.

👑 /upgrade_plus
Unlock VIP predictions.

👥 /referral
Invite friends and earn rewards.

📊 /stats
View your referral progress.

📅 /myplan
Check your subscription.

📚 /history
View previous AI predictions.

❓ /help
Need assistance?
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
    plan = check_subscription(update.effective_user.id)

    bets = ai_model(plan)

    print("========== /predict ==========")
    print("BETS RETURNED:", bets)
    print("TOTAL BETS:", len(bets))

    print("BETS RETURNED:", bets)

    if not bets:
        await update.message.reply_text(
            "⚠️ No strong edge found today."
        )
        return

    message = "🔥 EdgeClass AI Predictions\n\n"

    if plan == "vip":
        bets = bets[:3]

    elif plan == "premium":
        bets = bets[:5]

    else:
        bets = bets[:1]

    for bet in bets:

        save_prediction(
            bet["fixture_id"],
            bet["match"],
            bet["prediction"],
            bet["confidence"],
            bet["odds"],
            bet["league"],
            bet["kickoff"],

            bet["grade"],
            bet["value"],
            bet["edge"],
            bet["reasoning"],
            bet["home_rating"],
            bet["away_rating"],

            tier=plan
        )

        if plan == "free":

            message += (
                f"⚽ {bet['match']}\n"
                f"🏆 {bet['league']}\n"
                f"🕒 {bet['kickoff']} WAT\n\n"

                f"🎯 Prediction\n"
                f"{bet['prediction']}\n\n"

                f"📈 Confidence\n"
                f"{bet['confidence']}%\n\n"

                f"💰 Odds\n"
                f"{bet['odds']}\n\n"

               "━━━━━━━━━━━━━━━━━━\n\n"
            )

        elif plan == "premium":

            message += (
                f"⭐ PREMIUM AI REPORT\n\n"

                f"⚽ {bet['match']}\n"
                f"🏆 {bet['league']}\n"
                f"🕒 {bet['kickoff']} WAT\n\n"

                f"🎯 Prediction\n"
                f"{bet['prediction']}\n\n"

                f"📈 Confidence\n"
                f"{bet['confidence']}%\n\n"

                f"🏅 Grade\n"
                f"{bet['grade']}\n\n"

                f"💎 Value\n"
                f"{bet['value']}\n\n"

                f"🔥 Edge\n"
                f"{bet['edge']}\n\n"

                f"🧠 AI Reasoning\n"
                f"{bet['reasoning']}\n\n"

                f"💰 Odds\n"
                f"{bet['odds']}\n\n"

                "━━━━━━━━━━━━━━━━━━\n\n"
            )

        else:

            message += (
            f"👑 VIP AI REPORT\n\n"

            f"⚽ {bet['match']}\n"
            f"🏆 {bet['league']}\n"
            f"🕒 {bet['kickoff']} WAT\n\n"

            f"🎯 Prediction\n"
            f"{bet['prediction']}\n\n"

            f"📈 Confidence\n"
            f"{bet['confidence']}%\n\n"

            f"🏅 Grade\n"
            f"{bet['grade']}\n\n"

            f"💎 Value\n"
            f"{bet['value']}\n\n"

            f"🔥 Edge\n"
            f"{bet['edge']}\n\n"

            "━━━━━━━━━━━━━━━━━━\n\n"

            "🏠 HOME AI\n\n"

            f"⭐ Overall Rating: {bet['home_rating']}\n"
            f"📊 Form: {bet['home_form']}\n"
            f"⚔ Attack: {bet['home_attack']}\n"
            f"🛡 Defense: {bet['home_defense']}\n"
            f"🚀 Momentum: {bet['home_momentum']}\n"
            f"🎯 xG: {bet['home_xg']}\n"
            f"🚫 xGA: {bet['home_xga']}\n\n"

            "━━━━━━━━━━━━━━━━━━\n\n"

            "✈️ AWAY AI\n\n"

            f"⭐ Overall Rating: {bet['away_rating']}\n"
            f"📊 Form: {bet['away_form']}\n"
            f"⚔ Attack: {bet['away_attack']}\n"
            f"🛡 Defense: {bet['away_defense']}\n"
            f"🚀 Momentum: {bet['away_momentum']}\n"
            f"🎯 xG: {bet['away_xg']}\n"
            f"🚫 xGA: {bet['away_xga']}\n\n"

            f"🧠 AI Reasoning\n"
            f"{bet['reasoning']}\n\n"

            f"💰 Odds\n"
            f"{bet['odds']}\n\n"

            "━━━━━━━━━━━━━━━━━━\n\n"
        )

    await update.message.reply_text(message)


async def accumulator(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if check_subscription(update.effective_user.id) == "free":
        await update.message.reply_text(
            "❌ Upgrade to Premium."
        )
        return
    plan = check_subscription(update.effective_user.id)

    bets = ai_model(plan)

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

        msg += (
            f"⚽ {bet['match']}\n"
            f"🎯 {bet['prediction']}\n"
            f"📈 {bet['confidence']}%\n"
            f"💰 {bet['odds']}\n\n"
        )

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

    print("===== HISTORY CALLED =====")

    if check_subscription(update.effective_user.id) == "free":
        await update.message.reply_text(
            "❌ Upgrade to Premium to view prediction history."
        )
        return

    plan = check_subscription(update.effective_user.id)

    rows = get_prediction_history(plan)

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
            actual_score,
            tier
        ) = row

        if tier == "vip":
           badge = "👑 VIP Prediction"

        elif tier == "premium":
             badge = "⭐ Premium Prediction"

        else:
            badge = "🆓 Free Prediction"

        message += (
            f"{badge}\n"
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


async def stats_ai(update: Update, context: ContextTypes.DEFAULT_TYPE):

    stats = get_prediction_stats()

    message = f"""
📊 EDGECLASS AI PERFORMANCE

━━━━━━━━━━━━━━━━━━

🎯 Total Predictions
{stats['total']}

✅ Wins
{stats['wins']}

❌ Losses
{stats['losses']}

📈 Strike Rate
{stats['strike_rate']}%
"""

    await update.message.reply_text(message)


def owner_panel():
    keyboard = [
        [
            InlineKeyboardButton("👥 Users", callback_data="admin_users"),
            InlineKeyboardButton("💎 Premium Manager", callback_data="admin_premium"),
        ],
        [
            InlineKeyboardButton("🔥 VIP Manager", callback_data="admin_vip"),
            InlineKeyboardButton("💳 Payments", callback_data="admin_payments"),
        ],
        [
            InlineKeyboardButton("🧠 AI Center", callback_data="admin_ai"),
            InlineKeyboardButton("📊 Analytics", callback_data="admin_analytics"),
        ],
        [
            InlineKeyboardButton("📢 Broadcast", callback_data="admin_broadcast"),
            InlineKeyboardButton("⚙️ Settings", callback_data="admin_settings"),
        ],
    ]

    return InlineKeyboardMarkup(keyboard)


def super_admin_panel():
    keyboard = [
        [
            InlineKeyboardButton("👥 Users", callback_data="admin_users"),
            InlineKeyboardButton("💎 Premium Manager", callback_data="admin_premium"),
        ],
        [
            InlineKeyboardButton("🔥 VIP Manager", callback_data="admin_vip"),
            InlineKeyboardButton("💳 Payments", callback_data="admin_payments"),
        ],
        [
            InlineKeyboardButton("🧠 AI Center", callback_data="admin_ai"),
            InlineKeyboardButton("📊 Analytics", callback_data="admin_analytics"),
        ],
        [
            InlineKeyboardButton("📢 Broadcast", callback_data="admin_broadcast"),
        ],
    ]

    return InlineKeyboardMarkup(keyboard)


def premium_moderator_panel():
    keyboard = [
        [
            InlineKeyboardButton(
                "💎 Premium Users",
                callback_data="premium_users"
            )
        ],
        [
            InlineKeyboardButton(
                "➕ Upgrade Premium",
                callback_data="premium_upgrade"
            ),
            InlineKeyboardButton(
                "📅 Extend Premium",
                callback_data="premium_extend"
            ),
        ],
        [
            InlineKeyboardButton(
                "📢 Broadcast Premium",
                callback_data="premium_broadcast"
            )
        ],
        [
            InlineKeyboardButton(
                "📨 Premium Support",
                callback_data="premium_support"
            )
        ],
    ]

    return InlineKeyboardMarkup(keyboard)


async def admin_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):

    query = update.callback_query

    await query.answer()

    user_id = query.from_user.id
    action = query.data

    # =====================================================
    # SECURITY CHECK
    # =====================================================

    if not (
        is_owner(user_id)
        or is_super_admin(user_id)
        or is_premium_moderator(user_id)
    ):
        await query.edit_message_text(
            "❌ You are not authorized to use this panel."
        )
        return

    # =====================================================
    # OWNER / ADMIN ACTIONS
    # =====================================================

    if action == "admin_users":

        keyboard = [
            [
                InlineKeyboardButton(
                    "🔎 Find User",
                    callback_data="users_find"
                )
            ],
            [
                InlineKeyboardButton(
                    "📋 List Users",
                    callback_data="users_list"
                )
            ],
            [
                InlineKeyboardButton(
                    "💎 Premium Users",
                    callback_data="users_premium"
                )
            ],
            [
                InlineKeyboardButton(
                    "🔥 VIP Users",
                    callback_data="users_vip"
                )
            ],
            [
                InlineKeyboardButton(
                    "⬅️ Back",
                    callback_data="admin_home"
                )
            ],
        ]

        await query.edit_message_text(
            "👥 <b>USER MANAGEMENT</b>\n\n"
            "Choose an option:",
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

        return

    # =====================================================
    # PREMIUM MANAGER
    # =====================================================

    if action == "admin_premium":

        # IMPORTANT:
        # Owner and Super Admin can access this.
        # Premium Moderator can also access Premium management.

        if not (
            is_owner(user_id)
            or is_super_admin(user_id)
            or is_premium_moderator(user_id)
        ):
            await query.edit_message_text(
                "❌ Premium Manager access denied."
            )
            return

        keyboard = [
            [
                InlineKeyboardButton(
                    "👥 Premium Users",
                    callback_data="premium_users"
                )
            ],
            [
                InlineKeyboardButton(
                    "➕ Add Premium",
                    callback_data="premium_upgrade"
                )
            ],
            [
                InlineKeyboardButton(
                    "📅 Extend Premium",
                    callback_data="premium_extend"
                )
            ],
            [
                InlineKeyboardButton(
                    "📢 Premium Broadcast",
                    callback_data="premium_broadcast"
                )
            ],
            [
                InlineKeyboardButton(
                    "⬅️ Back",
                    callback_data="admin_home"
                )
            ],
        ]

        await query.edit_message_text(
            "💎 <b>PREMIUM MANAGER</b>\n\n"
            "Manage EdgeClass Premium members.",
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

        return

    # =====================================================
    # VIP MANAGER
    # =====================================================

    if action == "admin_vip":

        # VIP is restricted to owner/super admin.
        # Your brother's Premium Moderator role cannot enter here.

        if not (
            is_owner(user_id)
            or is_super_admin(user_id)
        ):
            await query.edit_message_text(
                "❌ VIP Manager access denied."
            )
            return

        keyboard = [
            [
                InlineKeyboardButton(
                    "👑 VIP Users",
                    callback_data="vip_users"
                )
            ],
            [
                InlineKeyboardButton(
                    "➕ Add VIP",
                    callback_data="vip_upgrade"
                )
            ],
            [
                InlineKeyboardButton(
                    "📅 Extend VIP",
                    callback_data="vip_extend"
                )
            ],
            [
                InlineKeyboardButton(
                    "📢 VIP Broadcast",
                    callback_data="vip_broadcast"
                )
            ],
            [
                InlineKeyboardButton(
                    "⬅️ Back",
                    callback_data="admin_home"
                )
            ],
        ]

        await query.edit_message_text(
            "🔥 <b>VIP MANAGER</b>\n\n"
            "Manage EdgeClass VIP members.",
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

        return

    # =====================================================
    # PAYMENTS
    # =====================================================

    if action == "admin_payments":

        if not (
            is_owner(user_id)
            or is_super_admin(user_id)
        ):
            await query.edit_message_text(
                "❌ Payments access denied."
            )
            return

        keyboard = [
            [
                InlineKeyboardButton(
                    "💳 Payment History",
                    callback_data="payments_history"
                )
            ],
            [
                InlineKeyboardButton(
                    "📊 Payment Statistics",
                    callback_data="payments_stats"
                )
            ],
            [
                InlineKeyboardButton(
                    "⬅️ Back",
                    callback_data="admin_home"
                )
            ],
        ]

        await query.edit_message_text(
            "💳 <b>PAYMENTS CENTER</b>\n\n"
            "Payment management tools.",
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

        return

    # =====================================================
    # AI CENTER
    # =====================================================

    if action == "admin_ai":

        if not (
            is_owner(user_id)
            or is_super_admin(user_id)
        ):
            await query.edit_message_text(
                "❌ AI Center access denied."
            )
            return

        keyboard = [
            [
                InlineKeyboardButton(
                    "🧠 Engine Statistics",
                    callback_data="ai_engine_stats"
                )
            ],
            [
                InlineKeyboardButton(
                    "⚖ Dynamic Weights",
                    callback_data="ai_weights"
                )
            ],
            [
                InlineKeyboardButton(
                    "📚 Learning Memory",
                    callback_data="ai_learning"
                )
            ],
            [
                InlineKeyboardButton(
                    "⬅️ Back",
                    callback_data="admin_home"
                )
            ],
        ]

        await query.edit_message_text(
            "🧠 <b>EDGECLASS AI CENTER</b>\n\n"
            "Monitor and manage the prediction intelligence system.",
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

        return

    # =====================================================
    # ANALYTICS
    # =====================================================

    if action == "admin_analytics":

        if not (
            is_owner(user_id)
            or is_super_admin(user_id)
        ):
            await query.edit_message_text(
                "❌ Analytics access denied."
            )
            return

        keyboard = [
            [
                InlineKeyboardButton(
                    "📊 Engine Performance",
                    callback_data="analytics_engines"
                )
            ],
            [
                InlineKeyboardButton(
                    "🎯 Prediction Accuracy",
                    callback_data="analytics_accuracy"
                )
            ],
            [
                InlineKeyboardButton(
                    "👥 User Statistics",
                    callback_data="analytics_users"
                )
            ],
            [
                InlineKeyboardButton(
                    "⬅️ Back",
                    callback_data="admin_home"
                )
            ],
        ]

        await query.edit_message_text(
            "📊 <b>EDGECLASS ANALYTICS</b>\n\n"
            "System performance and business analytics.",
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

        return

    # =====================================================
    # BROADCAST
    # =====================================================

    if action == "admin_broadcast":

        if not (
            is_owner(user_id)
            or is_super_admin(user_id)
        ):
            await query.edit_message_text(
                "❌ Broadcast access denied."
            )
            return

        keyboard = [
            [
                InlineKeyboardButton(
                    "📢 Broadcast Everyone",
                    callback_data="broadcast_all"
                )
            ],
            [
                InlineKeyboardButton(
                    "💎 Broadcast Premium",
                    callback_data="broadcast_premium"
                )
            ],
            [
                InlineKeyboardButton(
                    "🔥 Broadcast VIP",
                    callback_data="broadcast_vip"
                )
            ],
            [
                InlineKeyboardButton(
                    "⬅️ Back",
                    callback_data="admin_home"
                )
            ],
        ]

        await query.edit_message_text(
            "📢 <b>BROADCAST CENTER</b>\n\n"
            "Choose your audience.",
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

        return

    # =====================================================
    # BACK TO ADMIN HOME
    # =====================================================

    if action == "admin_home":

        keyboard = [
            [
                InlineKeyboardButton(
                    "👥 Users",
                    callback_data="admin_users"
                )
            ],
            [
                InlineKeyboardButton(
                    "💎 Premium Manager",
                    callback_data="admin_premium"
                )
            ],
            [
                InlineKeyboardButton(
                    "🔥 VIP Manager",
                    callback_data="admin_vip"
                )
            ],
            [
                InlineKeyboardButton(
                    "💳 Payments",
                    callback_data="admin_payments"
                )
            ],
            [
                InlineKeyboardButton(
                    "🧠 AI Center",
                    callback_data="admin_ai"
                )
            ],
            [
                InlineKeyboardButton(
                    "📊 Analytics",
                    callback_data="admin_analytics"
                )
            ],
            [
                InlineKeyboardButton(
                    "📢 Broadcast",
                    callback_data="admin_broadcast"
                )
            ],
        ]

        await query.edit_message_text(
            "🛡 <b>EDGECLASS ADMIN PANEL</b>\n\n"
            "Select a management area below:",
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

        return
    

async def show_admin_users(query):

    conn = get_connection()

    try:

        with conn.cursor() as cur:

            cur.execute(
                "SELECT COUNT(*) FROM users"
            )

            total_users = cur.fetchone()[0]

            cur.execute(
                "SELECT * FROM users LIMIT 10"
            )

            rows = cur.fetchall()

            columns = [
                column.name
                for column in cur.description
            ]

    finally:

        conn.close()

    text = (
        "👥 <b>EDGECLASS USERS</b>\n\n"
        f"Total users: <b>{total_users}</b>\n\n"
    )

    if not rows:

        text += "No users found."

    else:

        text += "<b>Recent users:</b>\n\n"

        for row in rows:

            data = dict(zip(columns, row))

            user_id = data.get("user_id", "Unknown")

            text += f"👤 <code>{user_id}</code>\n"

            # Show subscription if the database has it
            plan = data.get("plan")

            if plan:
                text += f"   Plan: {plan}\n"

            text += "\n"

    keyboard = [
        [
            InlineKeyboardButton(
                "⬅️ Back",
                callback_data="admin_back"
            )
        ]
    ]

    await query.edit_message_text(
        text,
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


async def show_premium_users(query):

    conn = get_connection()

    try:

        with conn.cursor() as cur:

            cur.execute(
                """
                SELECT *
                FROM users
                WHERE plan = 'premium'
                LIMIT 20
                """
            )

            rows = cur.fetchall()

            columns = [
                column.name
                for column in cur.description
            ]

    finally:

        conn.close()

    text = (
        "💎 <b>PREMIUM USERS</b>\n\n"
        f"Premium users found: <b>{len(rows)}</b>\n\n"
    )

    if not rows:

        text += "No Premium users found."

    else:

        for row in rows:

            data = dict(zip(columns, row))

            user_id = data.get("user_id", "Unknown")

            text += f"👤 <code>{user_id}</code>\n"

            username = data.get("username")

            if username:
                text += f"   @{username}\n"

            text += "\n"

    keyboard = [
        [
            InlineKeyboardButton(
                "⬅️ Back",
                callback_data="admin_back"
            )
        ]
    ]

    await query.edit_message_text(
        text,
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):

    await update.message.reply_text(
        """
🏆 EdgeClass AI

⚽ /edge_today
Today's free AI prediction.

🤖 /predict
Generate premium AI match predictions.

🎯 /accumulator
Receive a smart accumulator ticket.

💎 /pay
Upgrade to Premium.

👑 /upgrade_plus
Unlock VIP predictions.

👥 /referral
Invite friends and earn rewards.

📊 /stats
View your referral progress.

📅 /myplan
Check your subscription plan.

📚 /history
View previous AI predictions.

🛡 /admin
Open the Admin Dashboard.

❓ /help
Show available commands.
"""
    )    


# ================= DATABASE =================

init_db()

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
application.add_handler(CommandHandler("stats_ai", stats_ai))
application.add_handler(CommandHandler("admin", admin))

application.add_handler(
    CallbackQueryHandler(admin_callback, pattern=r"^admin:")
)

async def process_telegram_update(update_dict):
    await application.initialize()

    try:
        update = Update.de_json(update_dict, application.bot)
        await application.process_update(update)
    finally:
        await application.shutdown()