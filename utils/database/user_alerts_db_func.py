# 🌸────────────────────────────────────────────
#        💜 User Alerts Database Helpers 💜
# 🌸────────────────────────────────────────────

import asyncpg

from utils.loggers.pretty_logs import pretty_log

TABLE_NAME = "user_alerts"


# 💠────────────────────────────────────────────
# [🔍 FETCH] All alerts by alert_type
# ─────────────────────────────────────────────
async def fetch_all_alerts_by_type(bot, alert_type: str):
    """
    Fetch all users subscribed to a given alert type.
    """
    try:
        async with bot.pg_pool.acquire() as conn:
            rows = await conn.fetch(
                f"SELECT * FROM {TABLE_NAME} WHERE alert_type=$1 AND notify=TRUE",
                alert_type,
            )
        pretty_log("db", f"Fetched {len(rows)} alerts for type '{alert_type}'", bot=bot)
        return rows
    except Exception as e:
        pretty_log(
            "error", f"Failed to fetch alerts for type '{alert_type}': {e}", bot=bot
        )
        return []


# 💠────────────────────────────────────────────
# [🔍 FETCH] All alerts by user_id
# ─────────────────────────────────────────────
async def fetch_all_user_alerts(bot, user_id: int):
    """
    Fetch all alert rows for a single user.

    Args:
        bot: The Discord bot instance containing the PostgreSQL pool.
        user_id: The Discord user ID.

    Returns:
        List of asyncpg.Record representing all alerts for the user.
        Returns [] if none or on error.
    """
    try:
        async with bot.pg_pool.acquire() as conn:
            rows = await conn.fetch(
                f"SELECT * FROM {TABLE_NAME} WHERE user_id=$1", user_id
            )

        pretty_log("db", f"Fetched {len(rows)} alerts for user_id {user_id}", bot=bot)
        return rows

    except Exception as e:
        pretty_log(
            "error", f"Failed to fetch alerts for user_id {user_id}: {e}", bot=bot
        )
        return []


# 💠────────────────────────────────────────────
# [👤 FETCH] Single user alert by type
# ─────────────────────────────────────────────
async def fetch_user_alert_by_type(bot, user_id: int, alert_type: str):
    """
    Fetch a single user's alert entry for a given type.
    """
    try:
        async with bot.pg_pool.acquire() as conn:
            row = await conn.fetchrow(
                f"SELECT * FROM {TABLE_NAME} WHERE user_id=$1 AND alert_type=$2",
                user_id,
                alert_type,
            )
        if row:
            pretty_log(
                "db", f"Fetched alert '{alert_type}' for user_id {user_id}", bot=bot
            )
        return row
    except Exception as e:
        pretty_log(
            "error",
            f"Failed to fetch user alert ({alert_type}) for {user_id}: {e}",
            bot=bot,
        )
        return None


# 💠────────────────────────────────────────────
# [💀 REMOVE] Delete user alert by type
# ─────────────────────────────────────────────
async def remove_user_alert_by_type(bot, user_id: int, alert_type: str):
    """
    Remove a user's specific alert type.
    """
    try:
        async with bot.pg_pool.acquire() as conn:
            await conn.execute(
                f"DELETE FROM {TABLE_NAME} WHERE user_id=$1 AND alert_type=$2",
                user_id,
                alert_type,
            )
        pretty_log("db", f"Removed '{alert_type}' alert for user_id {user_id}", bot=bot)
    except Exception as e:
        pretty_log(
            "error",
            f"Failed to remove alert ({alert_type}) for {user_id}: {e}",
            bot=bot,
        )


# 💠────────────────────────────────────────────
# [🔄 UPDATE] Toggle or set notify column
# ─────────────────────────────────────────────
async def update_user_alert_notify(bot, user_id: int, alert_type: str, notify: bool):
    """
    Update the notify status (True/False) for a user’s alert type.
    Creates the row if it doesn't exist.
    """
    try:
        async with bot.pg_pool.acquire() as conn:
            await conn.execute(
                f"""
                INSERT INTO {TABLE_NAME} (user_id, user_name, alert_type, notify)
                VALUES ($1, '', $2, $3)
                ON CONFLICT (user_id, alert_type)
                DO UPDATE SET notify = EXCLUDED.notify
                """,
                user_id,
                alert_type,
                notify,
            )
        pretty_log(
            "db",
            f"Updated notify={notify} for '{alert_type}' alert (user_id {user_id})",
            bot=bot,
        )
    except Exception as e:
        pretty_log(
            "error",
            f"Failed to update notify for {alert_type} ({user_id}): {e}",
            bot=bot,
        )
