from __future__ import annotations

from typing import Any

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ContextTypes,
    ConversationHandler,
    MessageHandler,
    CallbackQueryHandler,
    filters,
)

from permissions import (
    is_owner,
    is_super_admin,
    is_premium_moderator,
)

from database import (
    get_connection,
    get_user,
    check_subscription,
    extend_plan,
)

try:
    from analytics import get_prediction_stats
except ImportError:
    get_prediction_stats = None


# ============================================================
# PREMIUM ADMIN CONVERSATION STATES
# ============================================================

PREMIUM_TARGET_USER = 1
PREMIUM_EXTEND_DAYS = 2


# ============================================================
# HELPERS
# ============================================================

def _is_admin(user_id: int | None) -> bool:
    if not user_id:
        return False

    return (
        is_owner(user_id)
        or is_super_admin(user_id)
        or is_premium_moderator(user_id)
    )


def _is_owner_or_super_admin(user_id: int | None) -> bool:
    if not user_id:
        return False

    return is_owner(user_id) or is_super_admin(user_id)


def _is_owner(user_id: int | None) -> bool:
    return bool(user_id and is_owner(user_id))


def _back_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("⬅️ Back", callback_data="admin:back")]
    ])


def _main_keyboard(user_id: int) -> InlineKeyboardMarkup:
    rows = [
        [
            InlineKeyboardButton("👥 Users", callback_data="admin:users"),
            InlineKeyboardButton("💎 Premium Manager", callback_data="admin:premium"),
        ],
        [
            InlineKeyboardButton("🔥 VIP Manager", callback_data="admin:vip"),
            InlineKeyboardButton("💳 Payments", callback_data="admin:payments"),
        ],
        [
            InlineKeyboardButton("🧠 AI Center", callback_data="admin:ai"),
            InlineKeyboardButton("📊 Analytics", callback_data="admin:analytics"),
        ],
        [
            InlineKeyboardButton("📢 Broadcast", callback_data="admin:broadcast"),
        ],
    ]

    if is_owner(user_id):
        rows.append([
            InlineKeyboardButton("⚙️ Settings", callback_data="admin:settings")
        ])

    return InlineKeyboardMarkup(rows)


def _escape_html(value: Any) -> str:
    """Small Telegram-HTML escape helper."""
    text = "" if value is None else str(value)
    return (
        text.replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
    )


def _row_to_dict(row, columns):
    return dict(zip(columns, row))


# ============================================================
# /admin
# ============================================================

async def admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Open the EdgeClass administration dashboard."""

    user = update.effective_user

    if not user or not _is_admin(user.id):
        if update.message:
            await update.message.reply_text(
                "❌ Unauthorized.\n\n"
                "You do not have permission to access the EdgeClass Admin Dashboard."
            )
        return

    role = "OWNER" if is_owner(user.id) else (
        "SUPER ADMIN" if is_super_admin(user.id) else "PREMIUM MODERATOR"
    )

    text = (
        "🛡 <b>EDGECLASS ADMIN DASHBOARD</b>\n\n"
        f"👤 Administrator: <b>{_escape_html(user.first_name)}</b>\n"
        f"🔐 Role: <b>{role}</b>\n\n"
        "Select an administration area below."
    )

    if update.message:
        await update.message.reply_text(
            text,
            parse_mode="HTML",
            reply_markup=_main_keyboard(user.id),
        )


async def show_admin_user_profile(query, target_user_id):
    """Display the complete profile of one user."""

    admin_id = query.from_user.id

    if not (is_owner(admin_id) or is_super_admin(admin_id)):
        await query.answer(
            "You do not have permission to view user profiles.",
            show_alert=True,
        )
        return

    from database import get_admin_user_profile

    row = get_admin_user_profile(target_user_id)

    if not row:
        await query.answer(
            "User not found.",
            show_alert=True,
        )
        return

    (
        uid,
        plan,
        joined_date,
        expiry_date,
        referrals,
        successful_referrals,
        last_payment_reference,
        last_payment_amount,
        last_payment_date,
    ) = row

    plan = plan or "free"

    if plan == "vip":
        plan_icon = "🔥"
    elif plan == "premium":
        plan_icon = "⭐"
    else:
        plan_icon = "🆓"

    text = (
        "👤 <b>USER PROFILE</b>\n\n"
        f"🆔 User ID: <code>{_escape_html(uid)}</code>\n\n"
        f"📋 <b>ACCOUNT</b>\n"
        f"Plan: {plan_icon} <b>{_escape_html(plan.upper())}</b>\n"
        f"Joined: {_escape_html(joined_date or 'Unknown')}\n"
        f"Expires: {_escape_html(expiry_date or 'Unlimited')}\n\n"
        f"👥 <b>REFERRALS</b>\n"
        f"Total: <b>{referrals or 0}</b>\n"
        f"Successful: <b>{successful_referrals or 0}</b>\n\n"
        f"💳 <b>LATEST PAYMENT</b>\n"
        f"Reference: "
        f"<code>{_escape_html(last_payment_reference or 'None')}</code>\n"
        f"Amount: ₦{(last_payment_amount or 0):,}\n"
        f"Date: {_escape_html(last_payment_date or 'None')}\n"
    )

    keyboard = [
        [
            InlineKeyboardButton(
                "⚙️ Actions",
                callback_data=f"admin:user:actions:{uid}",
            )
        ],
        [
            InlineKeyboardButton(
                "💳 Payment History",
                callback_data=f"admin:user:payments:{uid}",
            )
        ],
        [
            InlineKeyboardButton(
                "⬅️ Users",
                callback_data="admin:users",
            )
        ],
    ]

    await query.edit_message_text(
        text,
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup(keyboard),
    )


# ============================================================
# USERS
# ============================================================

async def show_admin_users(query):
    """Main User Management screen."""

    user_id = query.from_user.id

    # Users are sensitive admin functionality.
    # Premium Moderators should NOT have access here.
    if not (is_owner(user_id) or is_super_admin(user_id)):
        await query.answer(
            "You do not have permission to manage users.",
            show_alert=True,
        )
        return

    from database import get_admin_user_counts

    counts = get_admin_user_counts()

    text = (
        "👥 <b>USER MANAGEMENT</b>\n\n"
        f"👥 Total Users: <b>{counts['total']}</b>\n"
        f"🆓 Free: <b>{counts['free']}</b>\n"
        f"⭐ Premium: <b>{counts['premium']}</b>\n"
        f"🔥 VIP: <b>{counts['vip']}</b>\n\n"
        "Select an action:"
    )

    keyboard = [
        [
            InlineKeyboardButton(
                "🔎 Find User",
                callback_data="admin:users:find",
            )
        ],
        [
            InlineKeyboardButton(
                "👥 All Users",
                callback_data="admin:users:all",
            )
        ],
        [
            InlineKeyboardButton(
                "⭐ Premium Users",
                callback_data="admin:users:premium",
            ),
            InlineKeyboardButton(
                "🔥 VIP Users",
                callback_data="admin:users:vip",
            ),
        ],
        [
            InlineKeyboardButton(
                "⬅️ Back",
                callback_data="admin:back",
            )
        ],
    ]

    await query.edit_message_text(
        text,
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup(keyboard),
    )


async def show_admin_user_profile(query, target_user_id):
    """Display the complete profile of one user."""

    admin_id = query.from_user.id

    if not (is_owner(admin_id) or is_super_admin(admin_id)):
        await query.answer(
            "You do not have permission to view user profiles.",
            show_alert=True,
        )
        return

    from database import get_admin_user_profile

    row = get_admin_user_profile(target_user_id)

    if not row:
        await query.answer(
            "User not found.",
            show_alert=True,
        )
        return

    (
        uid,
        plan,
        joined_date,
        expiry_date,
        referrals,
        successful_referrals,
        last_payment_reference,
        last_payment_amount,
        last_payment_date,
    ) = row

    plan = plan or "free"

    if plan == "vip":
        plan_icon = "🔥"
    elif plan == "premium":
        plan_icon = "⭐"
    else:
        plan_icon = "🆓"

    text = (
        "👤 <b>USER PROFILE</b>\n\n"
        f"🆔 User ID: <code>{_escape_html(uid)}</code>\n\n"
        f"📋 <b>ACCOUNT</b>\n"
        f"Plan: {plan_icon} <b>{_escape_html(plan.upper())}</b>\n"
        f"Joined: {_escape_html(joined_date or 'Unknown')}\n"
        f"Expires: {_escape_html(expiry_date or 'Unlimited')}\n\n"
        f"👥 <b>REFERRALS</b>\n"
        f"Total: <b>{referrals or 0}</b>\n"
        f"Successful: <b>{successful_referrals or 0}</b>\n\n"
        f"💳 <b>LATEST PAYMENT</b>\n"
        f"Reference: "
        f"<code>{_escape_html(last_payment_reference or 'None')}</code>\n"
        f"Amount: ₦{(last_payment_amount or 0):,}\n"
        f"Date: {_escape_html(last_payment_date or 'None')}\n"
    )

    keyboard = [
        [
            InlineKeyboardButton(
                "⚙️ Actions",
                callback_data=f"admin:user:actions:{uid}",
            )
        ],
        [
            InlineKeyboardButton(
                "💳 Payment History",
                callback_data=f"admin:user:payments:{uid}",
            )
        ],
        [
            InlineKeyboardButton(
                "⬅️ Users",
                callback_data="admin:users",
            )
        ],
    ]

    await query.edit_message_text(
        text,
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup(keyboard),
    )


async def show_all_users(query, page=0):
    """Display users with pagination."""

    user_id = query.from_user.id

    if not (is_owner(user_id) or is_super_admin(user_id)):
        await query.answer(
            "You do not have permission to manage users.",
            show_alert=True,
        )
        return

    from database import get_admin_users

    limit = 10
    offset = page * limit

    rows = get_admin_users(
        plan=None,
        limit=limit,
        offset=offset,
    )

    keyboard = []

    text = (
        "👥 <b>ALL USERS</b>\n\n"
        f"Page: <b>{page + 1}</b>\n\n"
    )

    if not rows:
        text += "No users found."
    else:
        for row in rows:
            (
                uid,
                plan,
                joined_date,
                expiry_date,
                referrals,
                successful_referrals,
            ) = row

            text += (
                f"👤 <code>{_escape_html(uid)}</code>\n"
                f"   Plan: <b>{_escape_html(plan)}</b>\n"
                f"   Joined: {_escape_html(joined_date or 'Unknown')}\n"
                f"   Referrals: {referrals or 0}\n"
                f"   Successful: {successful_referrals or 0}\n"
            )

            if expiry_date:
                text += (
                    f"   Expires: {_escape_html(expiry_date)}\n"
                )

            text += "\n"

            keyboard.append([
                InlineKeyboardButton(
                    f"👤 View {uid}",
                    callback_data=f"admin:user:{uid}",
                )
            ])

    navigation = []

    if page > 0:
        navigation.append(
            InlineKeyboardButton(
                "⬅️ Previous",
                callback_data=f"admin:users:all:{page - 1}",
            )
        )

    if len(rows) == limit:
        navigation.append(
            InlineKeyboardButton(
                "Next ➡️",
                callback_data=f"admin:users:all:{page + 1}",
            )
        )

    if navigation:
        keyboard.append(navigation)

    keyboard.append([
        InlineKeyboardButton(
            "⬅️ User Management",
            callback_data="admin:users",
        )
    ])

    await query.edit_message_text(
        text,
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup(keyboard),
    )  


async def show_admin_plan_users(query, plan):
    """Display users belonging to a specific subscription plan."""

    user_id = query.from_user.id

    if not (is_owner(user_id) or is_super_admin(user_id)):
        await query.answer(
            "You do not have permission to manage users.",
            show_alert=True,
        )
        return

    from database import get_admin_users

    rows = get_admin_users(
        plan=plan,
        limit=20,
        offset=0,
    )

    labels = {
        "free": "🆓 FREE USERS",
        "premium": "⭐ PREMIUM USERS",
        "vip": "🔥 VIP USERS",
    }

    title = labels.get(plan, "👥 USERS")

    text = (
        f"<b>{title}</b>\n\n"
        f"Users found: <b>{len(rows)}</b>\n\n"
    )

    if not rows:
        text += "No users found."
    else:
        for row in rows:
            (
                uid,
                user_plan,
                joined_date,
                expiry_date,
                referrals,
                successful_referrals,
            ) = row

            text += (
                f"👤 <code>{_escape_html(uid)}</code>\n"
                f"   Plan: <b>{_escape_html(user_plan)}</b>\n"
            )

            if expiry_date:
                text += (
                    f"   Expires: "
                    f"{_escape_html(expiry_date)}\n"
                )

            text += (
                f"   Referrals: {referrals or 0}\n"
                f"   Successful: {successful_referrals or 0}\n\n"
            )

    keyboard = [
        [
            InlineKeyboardButton(
                "⬅️ User Management",
                callback_data="admin:users",
            )
        ]
    ]

    await query.edit_message_text(
        text,
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup(keyboard),
    )     


# ============================================================
# PREMIUM
# ============================================================

async def show_premium_users(query):
    """Display Premium subscribers."""

    user_id = query.from_user.id

    if not _is_admin(user_id):
        await query.answer("Unauthorized.", show_alert=True)
        return

    conn = get_connection()

    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT *
                FROM users
                WHERE plan = 'premium'
                ORDER BY user_id DESC
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
            data = _row_to_dict(row, columns)

            uid = data.get("user_id", "Unknown")
            username = data.get("username")
            expiry = data.get("expiry_date")

            text += f"👤 <code>{_escape_html(uid)}</code>\n"

            if username:
                text += f"   @{_escape_html(username)}\n"

            if expiry:
                text += f"   Expires: {_escape_html(expiry)}\n"

            text += "\n"

    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("➕ Upgrade Premium", callback_data="admin:premium_upgrade")],
        [InlineKeyboardButton("📅 Extend Premium", callback_data="admin:premium_extend")],
        [InlineKeyboardButton("⬅️ Back", callback_data="admin:back")],
    ])

    await query.edit_message_text(
        text,
        parse_mode="HTML",
        reply_markup=keyboard,
    )


# ============================================================
# VIP
# ============================================================

async def show_vip_users(query):
    """Display VIP subscribers."""

    user_id = query.from_user.id

    if not _is_admin(user_id):
        await query.answer("Unauthorized.", show_alert=True)
        return

    conn = get_connection()

    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT *
                FROM users
                WHERE plan = 'vip'
                ORDER BY user_id DESC
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
        "🔥 <b>VIP USERS</b>\n\n"
        f"VIP users found: <b>{len(rows)}</b>\n\n"
    )

    if not rows:
        text += "No VIP users found."
    else:
        for row in rows:
            data = _row_to_dict(row, columns)

            uid = data.get("user_id", "Unknown")
            username = data.get("username")
            expiry = data.get("expiry_date")

            text += f"👤 <code>{_escape_html(uid)}</code>\n"

            if username:
                text += f"   @{_escape_html(username)}\n"

            if expiry:
                text += f"   Expires: {_escape_html(expiry)}\n"

            text += "\n"

    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("⬅️ Back", callback_data="admin:back")],
    ])

    await query.edit_message_text(
        text,
        parse_mode="HTML",
        reply_markup=keyboard,
    )


# ============================================================
# PAYMENTS
# ============================================================

async def show_payments(query):
    """Display payment-related overview without assuming a payment table exists."""

    user_id = query.from_user.id

    if not _is_admin(user_id):
        await query.answer("Unauthorized.", show_alert=True)
        return

    conn = get_connection()

    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT
                    COUNT(*) AS total,
                    SUM(CASE WHEN plan = 'premium' THEN 1 ELSE 0 END) AS premium,
                    SUM(CASE WHEN plan = 'vip' THEN 1 ELSE 0 END) AS vip
                FROM users
                """
            )

            total, premium, vip = cur.fetchone()
    finally:
        conn.close()

    premium = premium or 0
    vip = vip or 0

    text = (
        "💳 <b>PAYMENTS CENTER</b>\n\n"
        f"👥 Registered users: <b>{total}</b>\n"
        f"💎 Premium subscribers: <b>{premium}</b>\n"
        f"🔥 VIP subscribers: <b>{vip}</b>\n\n"
        "Payment initialization is handled by <code>payments.py</code>.\n"
        "Use this section for subscription/payment monitoring."
    )

    await query.edit_message_text(
        text,
        parse_mode="HTML",
        reply_markup=_back_keyboard(),
    )


# ============================================================
# AI CENTER
# ============================================================

async def show_ai_center(query):
    """AI/prediction control center."""

    user_id = query.from_user.id

    if not _is_admin(user_id):
        await query.answer("Unauthorized.", show_alert=True)
        return

    text = (
        "🧠 <b>EDGECLASS AI CENTER</b>\n\n"
        "Prediction architecture:\n\n"
        "⚽ <b>Free</b>\n"
        "• Limited prediction output\n\n"
        "⭐ <b>Premium</b>\n"
        "• Extended AI report\n"
        "• Grade\n"
        "• Value\n"
        "• Edge\n"
        "• AI reasoning\n\n"
        "👑 <b>VIP</b>\n"
        "• Deep AI report\n"
        "• Home/away ratings\n"
        "• Form\n"
        "• Attack\n"
        "• Defense\n"
        "• Momentum\n"
        "• xG / xGA\n\n"
        "Predictions are generated through <code>football_api.ai_model()</code>."
    )

    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("📊 AI Performance", callback_data="admin:ai_stats")],
        [InlineKeyboardButton("⬅️ Back", callback_data="admin:back")],
    ])

    await query.edit_message_text(
        text,
        parse_mode="HTML",
        reply_markup=keyboard,
    )


async def show_ai_stats(query):
    """Display prediction performance from analytics.py."""

    user_id = query.from_user.id

    if not _is_admin(user_id):
        await query.answer("Unauthorized.", show_alert=True)
        return

    if get_prediction_stats is None:
        await query.edit_message_text(
            "⚠️ Analytics module is unavailable.",
            reply_markup=_back_keyboard(),
        )
        return

    try:
        stats = get_prediction_stats()
    except Exception as exc:
        await query.edit_message_text(
            "⚠️ Unable to load AI performance.\n\n"
            f"<code>{_escape_html(exc)}</code>",
            parse_mode="HTML",
            reply_markup=_back_keyboard(),
        )
        return

    text = (
        "📊 <b>EDGECLASS AI PERFORMANCE</b>\n\n"
        "━━━━━━━━━━━━━━━━━━\n\n"
        f"🎯 Total Predictions\n<b>{stats.get('total', 0)}</b>\n\n"
        f"✅ Wins\n<b>{stats.get('wins', 0)}</b>\n\n"
        f"❌ Losses\n<b>{stats.get('losses', 0)}</b>\n\n"
        f"📈 Strike Rate\n<b>{stats.get('strike_rate', 0)}%</b>\n"
    )

    await query.edit_message_text(
        text,
        parse_mode="HTML",
        reply_markup=_back_keyboard(),
    )


# ============================================================
# ANALYTICS
# ============================================================

async def show_analytics(query):
    """Show high-level database analytics."""

    user_id = query.from_user.id

    if not _is_admin(user_id):
        await query.answer("Unauthorized.", show_alert=True)
        return

    conn = get_connection()

    try:
        with conn.cursor() as cur:
            cur.execute("SELECT COUNT(*) FROM users")
            users = cur.fetchone()[0] or 0

            cur.execute(
                """
                SELECT
                    SUM(CASE WHEN plan = 'free' THEN 1 ELSE 0 END),
                    SUM(CASE WHEN plan = 'premium' THEN 1 ELSE 0 END),
                    SUM(CASE WHEN plan = 'vip' THEN 1 ELSE 0 END)
                FROM users
                """
            )

            free, premium, vip = cur.fetchone()

    finally:
        conn.close()

    free = free or 0
    premium = premium or 0
    vip = vip or 0

    text = (
        "📊 <b>EDGECLASS ANALYTICS</b>\n\n"
        "━━━━━━━━━━━━━━━━━━\n\n"
        f"👥 Total Users\n<b>{users}</b>\n\n"
        f"🆓 Free Users\n<b>{free}</b>\n\n"
        f"⭐ Premium Users\n<b>{premium}</b>\n\n"
        f"👑 VIP Users\n<b>{vip}</b>\n\n"
        "━━━━━━━━━━━━━━━━━━"
    )

    await query.edit_message_text(
        text,
        parse_mode="HTML",
        reply_markup=_back_keyboard(),
    )


# ============================================================
# BROADCAST
# ============================================================

async def show_broadcast(query):
    """Broadcast menu.

    Actual broadcast sending is intentionally kept separate from this
    dashboard because the bot currently does not expose a confirmed
    broadcast database/API contract in the supplied source.
    """

    user_id = query.from_user.id

    if not _is_admin(user_id):
        await query.answer("Unauthorized.", show_alert=True)
        return

    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("📢 Broadcast All", callback_data="admin:broadcast_all")],
        [InlineKeyboardButton("⭐ Broadcast Premium", callback_data="admin:broadcast_premium")],
        [InlineKeyboardButton("👑 Broadcast VIP", callback_data="admin:broadcast_vip")],
        [InlineKeyboardButton("⬅️ Back", callback_data="admin:back")],
    ])

    await query.edit_message_text(
        "📢 <b>BROADCAST CENTER</b>\n\n"
        "Choose the audience for the broadcast.\n\n"
        "The dashboard is ready for broadcast handling, but no "
        "broadcast-storage contract was supplied in the current "
        "bot/database source.",
        parse_mode="HTML",
        reply_markup=keyboard,
    )


# ============================================================
# SETTINGS
# ============================================================

async def show_settings(query):
    """Owner-only settings area."""

    user_id = query.from_user.id

    if not _is_owner(user_id):
        await query.answer(
            "Owner access required.",
            show_alert=True,
        )
        return

    text = (
        "⚙️ <b>EDGECLASS SETTINGS</b>\n\n"
        "🔐 Access control\n"
        "• Owner\n"
        "• Super Admin\n"
        "• Premium Moderator\n\n"
        "💎 Premium price: configured in <code>config.py</code>\n"
        "🔥 VIP price: configured in <code>config.py</code>\n\n"
        "⚠️ Settings are intentionally read-only here until the "
        "project's configuration mutation interface is defined."
    )

    await query.edit_message_text(
        text,
        parse_mode="HTML",
        reply_markup=_back_keyboard(),
    )


# ============================================================
# SUB-MENU PLACEHOLDERS
# ============================================================

async def show_premium_upgrade(query):
    if not _is_admin(query.from_user.id):
        await query.answer("Unauthorized.", show_alert=True)
        return

    await query.edit_message_text(
        "➕ <b>PREMIUM UPGRADE</b>\n\n"
        "Premium upgrades are currently handled through <code>/pay</code> "
        "and <code>payments.py</code>.",
        parse_mode="HTML",
        reply_markup=_back_keyboard(),
    )


async def show_premium_extend(query):
    """Start the Premium extension workflow."""

    user_id = query.from_user.id

    if not _is_admin(user_id):
        await query.answer("Unauthorized.", show_alert=True)
        return ConversationHandler.END

    await query.edit_message_text(
        "📅 <b>EXTEND PREMIUM</b>\n\n"
        "Please send the <b>Telegram User ID</b> of the user "
        "whose Premium/VIP subscription you want to extend.\n\n"
        "Example:\n"
        "<code>123456789</code>\n\n"
        "Send /cancel to stop.",
        parse_mode="HTML",
    )

    return PREMIUM_TARGET_USER


async def receive_premium_target_user(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    """Receive and validate the Telegram user ID."""

    user_id = update.effective_user.id

    if not _is_admin(user_id):
        await update.message.reply_text(
            "❌ Unauthorized."
        )
        return ConversationHandler.END

    raw_user_id = (update.message.text or "").strip()

    try:
        target_user_id = int(raw_user_id)
    except ValueError:
        await update.message.reply_text(
            "❌ Invalid User ID.\n\n"
            "Please send a numeric Telegram User ID.\n\n"
            "Example:\n"
            "<code>123456789</code>\n\n"
            "Send /cancel to stop.",
            parse_mode="HTML",
        )
        return PREMIUM_TARGET_USER

    user = get_user(target_user_id)

    if not user:
        await update.message.reply_text(
            "❌ <b>USER NOT FOUND</b>\n\n"
            f"User ID <code>{target_user_id}</code> "
            "does not exist in the EdgeClass database.\n\n"
            "Please send another User ID or /cancel.",
            parse_mode="HTML",
        )
        return PREMIUM_TARGET_USER

    plan, joined, expiry = user

    if plan not in ("premium", "vip"):
        await update.message.reply_text(
            "❌ <b>USER IS NOT PREMIUM/VIP</b>\n\n"
            f"User ID: <code>{target_user_id}</code>\n"
            f"Current plan: <b>{_escape_html(plan)}</b>\n\n"
            "Only Premium or VIP subscriptions can be extended.",
            parse_mode="HTML",
        )
        return PREMIUM_TARGET_USER

    context.user_data["premium_target_user"] = target_user_id
    context.user_data["premium_target_plan"] = plan

    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton(
                "📅 30 Days",
                callback_data="admin:premium_extend:30",
            ),
            InlineKeyboardButton(
                "📅 60 Days",
                callback_data="admin:premium_extend:60",
            ),
        ],
        [
            InlineKeyboardButton(
                "📅 90 Days",
                callback_data="admin:premium_extend:90",
            ),
        ],
        [
            InlineKeyboardButton(
                "❌ Cancel",
                callback_data="admin:premium_extend:cancel",
            ),
        ],
    ])

    expiry_text = expiry or "No expiry"

    await update.message.reply_text(
        "✅ <b>USER FOUND</b>\n\n"
        f"👤 User ID: <code>{target_user_id}</code>\n"
        f"💎 Plan: <b>{_escape_html(plan.upper())}</b>\n"
        f"📅 Current expiry: <b>{_escape_html(expiry_text)}</b>\n\n"
        "Choose the extension period:",
        parse_mode="HTML",
        reply_markup=keyboard,
    )

    return PREMIUM_EXTEND_DAYS


async def handle_premium_extend(
    query,
    context: ContextTypes.DEFAULT_TYPE,
    days: int,
):
    """Extend the selected Premium/VIP user's subscription."""

    admin_id = query.from_user.id

    if not _is_admin(admin_id):
        await query.answer(
            "Unauthorized.",
            show_alert=True,
        )
        return ConversationHandler.END

    target_user_id = context.user_data.get(
        "premium_target_user"
    )

    plan = context.user_data.get(
        "premium_target_plan"
    )

    if not target_user_id:
        await query.edit_message_text(
            "❌ No target user selected.",
            reply_markup=_back_keyboard(),
        )
        return ConversationHandler.END

    success = extend_plan(
        target_user_id,
        days=days,
    )

    if not success:
        await query.edit_message_text(
            "❌ <b>EXTENSION FAILED</b>\n\n"
            f"User ID: <code>{target_user_id}</code>\n\n"
            "The user must exist and have an active "
            "Premium or VIP plan.",
            parse_mode="HTML",
            reply_markup=_back_keyboard(),
        )

        context.user_data.pop(
            "premium_target_user",
            None,
        )
        context.user_data.pop(
            "premium_target_plan",
            None,
        )

        return ConversationHandler.END

    await query.edit_message_text(
        "✅ <b>SUBSCRIPTION EXTENDED</b>\n\n"
        f"👤 User: <code>{target_user_id}</code>\n"
        f"💎 Plan: <b>{_escape_html(plan.upper())}</b>\n"
        f"📅 Extension: <b>{days} days</b>\n\n"
        "The subscription expiry has been updated successfully.",
        parse_mode="HTML",
        reply_markup=_back_keyboard(),
    )

    context.user_data.pop(
        "premium_target_user",
        None,
    )
    context.user_data.pop(
        "premium_target_plan",
        None,
    )

    return ConversationHandler.END


async def cancel_premium_extension(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    """Cancel the Premium extension workflow."""

    context.user_data.pop(
        "premium_target_user",
        None,
    )

    context.user_data.pop(
        "premium_target_plan",
        None,
    )

    await update.message.reply_text(
        "❌ Premium extension cancelled."
    )

    return ConversationHandler.END


async def show_broadcast_action(query, audience: str):
    if not _is_admin(query.from_user.id):
        await query.answer("Unauthorized.", show_alert=True)
        return

    labels = {
        "all": "ALL USERS",
        "premium": "PREMIUM USERS",
        "vip": "VIP USERS",
    }

    label = labels.get(audience, "USERS")

    await query.edit_message_text(
        f"📢 <b>BROADCAST → {label}</b>\n\n"
        "Broadcast sending is not executed by this screen because "
        "the supplied project code does not define the message-storage "
        "or broadcast workflow yet.",
        parse_mode="HTML",
        reply_markup=_back_keyboard(),
    )


# ============================================================
# PREMIUM EXTENSION CONVERSATION HANDLER
# ============================================================

premium_extension_conversation = ConversationHandler(
    entry_points=[
        CallbackQueryHandler(
            show_premium_extend,
            pattern=r"^admin:premium_extend$",
        )
    ],
    states={
        PREMIUM_TARGET_USER: [
            MessageHandler(
                filters.TEXT & ~filters.COMMAND,
                receive_premium_target_user,
            )
        ],
        PREMIUM_EXTEND_DAYS: [
            CallbackQueryHandler(
                lambda update, context:
                    handle_premium_extend(
                        update.callback_query,
                        context,
                        30,
                    ),
                pattern=r"^admin:premium_extend:30$",
            ),
            CallbackQueryHandler(
                lambda update, context:
                    handle_premium_extend(
                        update.callback_query,
                        context,
                        60,
                    ),
                pattern=r"^admin:premium_extend:60$",
            ),
            CallbackQueryHandler(
                lambda update, context:
                    handle_premium_extend(
                        update.callback_query,
                        context,
                        90,
                    ),
                pattern=r"^admin:premium_extend:90$",
            ),
            CallbackQueryHandler(
                cancel_premium_extension,
                pattern=r"^admin:premium_extend:cancel$",
            ),
        ],
    },
    fallbacks=[
        MessageHandler(
            filters.COMMAND & filters.Regex(r"^/cancel$"),
            cancel_premium_extension,
        ),
    ],
    allow_reentry=True,
)


# ============================================================
# CALLBACK ROUTER
# ============================================================

async def admin_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Central callback router for the EdgeClass admin dashboard."""

    query = update.callback_query

    if not query:
        return

    await query.answer()

    user_id = query.from_user.id

    if not _is_admin(user_id):
        await query.edit_message_text(
            "❌ Unauthorized.\n\n"
            "You do not have permission to use the Admin Dashboard."
        )
        return

    data = query.data or ""

    # Main dashboard
    if data in ("admin:back", "admin:home"):
        role = (
            "OWNER"
            if is_owner(user_id)
            else "SUPER ADMIN"
            if is_super_admin(user_id)
            else "PREMIUM MODERATOR"
        )

        await query.edit_message_text(
            "🛡 <b>EDGECLASS ADMIN DASHBOARD</b>\n\n"
            f"🔐 Role: <b>{role}</b>\n\n"
            "Select an administration area below.",
            parse_mode="HTML",
            reply_markup=_main_keyboard(user_id),
        )
        return

    # Main sections
    if data == "admin:users":
        await show_admin_users(query)
        return

    if data.startswith("admin:user:"):
        parts = data.split(":")

        if len(parts) == 3:
            try:
                target_user_id = int(parts[2])
            except ValueError:
                await query.answer(
                    "Invalid user ID.",
                    show_alert=True,
                )
                return

            await show_admin_user_profile(
                query,
                target_user_id,
            )
            return

    # --------------------------------------------------------
    # ALL USERS
    # --------------------------------------------------------

    if data == "admin:users:all":

        if not (is_owner(user_id) or is_super_admin(user_id)):
            await query.answer(
                "You do not have permission to manage users.",
                show_alert=True,
            )
            return

        await show_all_users(query, page=0)
        return

    # --------------------------------------------------------
    # ALL USERS PAGINATION
    # --------------------------------------------------------

    if data.startswith("admin:users:all:"):

        if not (is_owner(user_id) or is_super_admin(user_id)):
            await query.answer(
                "You do not have permission to manage users.",
                show_alert=True,
            )
            return

        try:
            page = int(data.rsplit(":", 1)[1])
        except ValueError:
            page = 0

        await show_all_users(query, page=page)
        return

    # --------------------------------------------------------
    # PREMIUM USERS
    # --------------------------------------------------------

    if data == "admin:users:premium":

        if not (is_owner(user_id) or is_super_admin(user_id)):
            await query.answer(
                "You do not have permission to manage users.",
                show_alert=True,
            )
            return

        await show_admin_plan_users(
            query,
            "premium",
        )
        return

    # --------------------------------------------------------
    # VIP USERS
    # --------------------------------------------------------

    if data == "admin:users:vip":

        if not (is_owner(user_id) or is_super_admin(user_id)):
            await query.answer(
                "You do not have permission to manage users.",
                show_alert=True,
            )
            return

        await show_admin_plan_users(
            query,
            "vip",
        )
        return

    if data == "admin:premium":
        await show_premium_users(query)
        return

    if data == "admin:vip":
        await show_vip_users(query)
        return

    if data == "admin:payments":
        await show_payments(query)
        return

    if data == "admin:ai":
        await show_ai_center(query)
        return

    if data == "admin:analytics":
        await show_analytics(query)
        return

    if data == "admin:broadcast":
        await show_broadcast(query)
        return

    if data == "admin:settings":
        await show_settings(query)
        return

    # AI submenu
    if data == "admin:ai_stats":
        await show_ai_stats(query)
        return

    # Premium submenu
    if data == "admin:premium_upgrade":
        await show_premium_upgrade(query)
        return

    # Broadcast submenu
    if data == "admin:broadcast_all":
        await show_broadcast_action(query, "all")
        return

    if data == "admin:premium_extend":
        await show_premium_extend(query)
        return

    if data == "admin:broadcast_premium":
        await show_broadcast_action(query, "premium")
        return

    if data == "admin:broadcast_vip":
        await show_broadcast_action(query, "vip")
        return

    # Backwards compatibility with the older callback format.
    legacy_map = {
        "admin_back": "admin:back",
        "admin_users": "admin:users",
        "admin_premium": "admin:premium",
        "admin_vip": "admin:vip",
        "admin_payments": "admin:payments",
        "admin_ai": "admin:ai",
        "admin_analytics": "admin:analytics",
        "admin_broadcast": "admin:broadcast",
        "admin_settings": "admin:settings",
        "premium_users": "admin:premium",
        "premium_upgrade": "admin:premium_upgrade",
        "premium_extend": "admin:premium_extend",
    }

    if data in legacy_map:
        mapped = legacy_map[data]

        if mapped == "admin:back":
            await query.edit_message_text(
                "🛡 <b>EDGECLASS ADMIN DASHBOARD</b>\n\n"
                "Select an administration area below.",
                parse_mode="HTML",
                reply_markup=_main_keyboard(user_id),
            )
        elif mapped == "admin:users":
            await show_admin_users(query)
        elif mapped == "admin:premium":
            await show_premium_users(query)
        elif mapped == "admin:vip":
            await show_vip_users(query)
        elif mapped == "admin:payments":
            await show_payments(query)
        elif mapped == "admin:ai":
            await show_ai_center(query)
        elif mapped == "admin:analytics":
            await show_analytics(query)
        elif mapped == "admin:broadcast":
            await show_broadcast(query)
        elif mapped == "admin:settings":
            await show_settings(query)
        elif mapped == "admin:premium_upgrade":
            await show_premium_upgrade(query)
        elif mapped == "admin:premium_extend":
            await show_premium_extend(query)

        return

    await query.edit_message_text(
        "⚠️ Unknown admin action.",
        reply_markup=_back_keyboard(),
    )