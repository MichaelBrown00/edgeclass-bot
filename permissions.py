from config import (
    OWNER_ID,
    SUPER_ADMIN_IDS,
    PREMIUM_MODERATOR_IDS
)


def is_owner(user_id: int) -> bool:
    """
    Returns True if the user is the Owner.
    """
    return user_id == OWNER_ID


def is_super_admin(user_id: int) -> bool:
    """
    Returns True if the user is a Super Admin.
    """
    return user_id in SUPER_ADMIN_IDS


def is_premium_moderator(user_id: int) -> bool:
    """
    Returns True if the user manages Premium users.
    """
    return user_id in PREMIUM_MODERATOR_IDS


def is_admin(user_id: int) -> bool:
    """
    Owner + Super Admin
    """
    return (
        is_owner(user_id)
        or is_super_admin(user_id)
    )


def can_manage_premium(user_id: int) -> bool:
    """
    Anyone allowed to manage Premium users.
    """
    return (
        is_owner(user_id)
        or is_super_admin(user_id)
        or is_premium_moderator(user_id)
    )


def can_manage_vip(user_id: int) -> bool:
    """
    VIP can only be managed by Owner and Super Admin.
    """
    return (
        is_owner(user_id)
        or is_super_admin(user_id)
    )


def can_access_ai(user_id: int) -> bool:
    """
    AI Center access.
    """
    return (
        is_owner(user_id)
        or is_super_admin(user_id)
    )


def can_access_payments(user_id: int) -> bool:
    """
    Payments Dashboard access.
    """
    return (
        is_owner(user_id)
        or is_super_admin(user_id)
    )


def can_broadcast(user_id: int) -> bool:
    """
    Broadcast messages.
    """
    return (
        is_owner(user_id)
        or is_super_admin(user_id)
        or is_premium_moderator(user_id)
    )