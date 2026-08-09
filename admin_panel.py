from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from permissions import (
    is_owner,
    is_super_admin,
    is_premium_moderator,
)


# ============================================================
# ADMIN DASHBOARD
# ============================================================

async def admin(update: Update, context: ContextTypes.DEFAULT_TYPE):

    user_id = update.effective_user.id

    # --------------------------------------------------------
    # OWNER
    # --------------------------------------------------------

    if is_owner(user_id):

        keyboard = [
            [
                InlineKeyboardButton("👥 Users", callback_data="admin:users"),
                InlineKeyboardButton("💎 Premium", callback_data="admin:premium"),
            ],
            [
                InlineKeyboardButton("🔥 VIP", callback_data="admin:vip"),
                InlineKeyboardButton("💳 Payments", callback_data="admin:payments"),
            ],
            [
                InlineKeyboardButton("🧠 AI Center", callback_data="admin:ai"),
                InlineKeyboardButton("📊 Analytics", callback_data="admin:analytics"),
            ],
            [
                InlineKeyboardButton("📢 Broadcast", callback_data="admin:broadcast"),
                InlineKeyboardButton("⚙️ Settings", callback_data="admin:settings"),
            ],
        ]

        text = (
            "🛡 <b>EDGECLASS OWNER PANEL</b>\n\n"
            "Welcome back, Owner.\n\n"
            "Select a section below:"
        )

    # --------------------------------------------------------
    # SUPER ADMIN
    # --------------------------------------------------------

    elif is_super_admin(user_id):

        keyboard = [
            [
                InlineKeyboardButton("👥 Users", callback_data="admin:users"),
                InlineKeyboardButton("💎 Premium", callback_data="admin:premium"),
            ],
            [
                InlineKeyboardButton("🔥 VIP", callback_data="admin:vip"),
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

        text = (
            "🛡 <b>EDGECLASS ADMIN PANEL</b>\n\n"
            "Welcome back, Admin.\n\n"
            "Select a section below:"
        )

    # --------------------------------------------------------
    # PREMIUM MODERATOR
    # --------------------------------------------------------

    elif is_premium_moderator(user_id):

        keyboard = [
            [
                InlineKeyboardButton(
                    "💎 Premium Users",
                    callback_data="admin:premium_users"
                )
            ],
            [
                InlineKeyboardButton(
                    "➕ Upgrade Premium",
                    callback_data="admin:premium_upgrade"
                ),
                InlineKeyboardButton(
                    "📅 Extend Premium",
                    callback_data="admin:premium_extend"
                ),
            ],
            [
                InlineKeyboardButton(
                    "📢 Broadcast Premium",
                    callback_data="admin:premium_broadcast"
                )
            ],
            [
                InlineKeyboardButton(
                    "📨 Premium Support",
                    callback_data="admin:premium_support"
                )
            ],
        ]

        text = (
            "💎 <b>PREMIUM MANAGER PANEL</b>\n\n"
            "Welcome back, Premium Moderator.\n\n"
            "You have access to Premium management only."
        )

    # --------------------------------------------------------
    # NOT AUTHORIZED
    # --------------------------------------------------------

    else:

        await update.message.reply_text(
            "❌ You are not authorized to access the Admin Panel."
        )

        return

    await update.message.reply_text(
        text,
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup(keyboard),
    )


# ============================================================
# ADMIN BUTTON HANDLER
# ============================================================

async def admin_callback(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):
    print("🔥 ADMIN CALLBACK RECEIVED")

    query = update.callback_query

    print("🔥 CALLBACK DATA:", query.data)
    print("🔥 CALLBACK USER:", query.from_user.id)

    await query.answer()

    user_id = query.from_user.id
    data = query.data

    # --------------------------------------------------------
    # SECURITY CHECK
    # --------------------------------------------------------

    if not (
        is_owner(user_id)
        or is_super_admin(user_id)
        or is_premium_moderator(user_id)
    ):
        await query.edit_message_text(
            "❌ You are not authorized to use this dashboard."
        )
        return

    # --------------------------------------------------------
    # USERS
    # --------------------------------------------------------

    if data == "admin:users":

        await query.edit_message_text(
            "👥 <b>USER MANAGEMENT</b>\n\n"
            "User management is coming next.",
            parse_mode="HTML",
        )
        return

    # --------------------------------------------------------
    # PREMIUM
    # --------------------------------------------------------

    if data in ("admin:premium", "admin:premium_users"):

        await query.edit_message_text(
            "💎 <b>PREMIUM MANAGER</b>\n\n"
            "Premium user management is coming next.",
            parse_mode="HTML",
        )
        return

    # --------------------------------------------------------
    # VIP
    # --------------------------------------------------------

    if data == "admin:vip":

        await query.edit_message_text(
            "🔥 <b>VIP MANAGER</b>\n\n"
            "VIP management is coming next.",
            parse_mode="HTML",
        )
        return

    # --------------------------------------------------------
    # PAYMENTS
    # --------------------------------------------------------

    if data == "admin:payments":

        await query.edit_message_text(
            "💳 <b>PAYMENTS</b>\n\n"
            "Payment management is coming next.",
            parse_mode="HTML",
        )
        return

    # --------------------------------------------------------
    # AI
    # --------------------------------------------------------

    if data == "admin:ai":

        await query.edit_message_text(
            "🧠 <b>AI CENTER</b>\n\n"
            "AI controls are coming next.",
            parse_mode="HTML",
        )
        return

    # --------------------------------------------------------
    # ANALYTICS
    # --------------------------------------------------------

    if data == "admin:analytics":

        await query.edit_message_text(
            "📊 <b>ANALYTICS</b>\n\n"
            "Analytics dashboard is coming next.",
            parse_mode="HTML",
        )
        return

    # --------------------------------------------------------
    # BROADCAST
    # --------------------------------------------------------

    if data == "admin:broadcast":

        await query.edit_message_text(
            "📢 <b>BROADCAST</b>\n\n"
            "Broadcast controls are coming next.",
            parse_mode="HTML",
        )
        return

    # --------------------------------------------------------
    # SETTINGS
    # --------------------------------------------------------

    if data == "admin:settings":

        if not is_owner(user_id):
            await query.edit_message_text(
                "❌ Owner access required."
            )
            return

        await query.edit_message_text(
            "⚙️ <b>SYSTEM SETTINGS</b>\n\n"
            "Owner-only settings are coming next.",
            parse_mode="HTML",
        )
        return

    # --------------------------------------------------------
    # PREMIUM MODERATOR ACTIONS
    # --------------------------------------------------------

    if data == "admin:premium_upgrade":

        if not (
            is_owner(user_id)
            or is_super_admin(user_id)
            or is_premium_moderator(user_id)
        ):
            await query.edit_message_text("❌ Access denied.")
            return

        await query.edit_message_text(
            "➕ <b>UPGRADE PREMIUM</b>\n\n"
            "Premium upgrade management is coming next.",
            parse_mode="HTML",
        )
        return

    if data == "admin:premium_extend":

        await query.edit_message_text(
            "📅 <b>EXTEND PREMIUM</b>\n\n"
            "Premium extension management is coming next.",
            parse_mode="HTML",
        )
        return

    if data == "admin:premium_broadcast":

        await query.edit_message_text(
            "📢 <b>PREMIUM BROADCAST</b>\n\n"
            "Premium-only broadcasting is coming next.",
            parse_mode="HTML",
        )
        return

    if data == "admin:premium_support":

        await query.edit_message_text(
            "📨 <b>PREMIUM SUPPORT</b>\n\n"
            "Premium support tools are coming next.",
            parse_mode="HTML",
        )
        return