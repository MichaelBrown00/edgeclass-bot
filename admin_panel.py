from telegram import InlineKeyboardButton, InlineKeyboardMarkup


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
            InlineKeyboardButton("⚙ System Settings", callback_data="admin_settings"),
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