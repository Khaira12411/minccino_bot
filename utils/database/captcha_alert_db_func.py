# 💠────────────────────────────────────────────
#   🐾 User Captcha Alert DB Functions
# 💠────────────────────────────────────────────

import asyncpg
from utils.loggers.pretty_logs import pretty_log

TABLE_NAME = "user_captcha_alert"


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 💾 Fetch all rows
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
async def fetch_all_captcha_alerts(bot) -> list[asyncpg.Record]:
    """
    Fetch all rows from the `user_captcha_alert` table.

    Args:
        bot: The Discord bot instance containing the PostgreSQL pool.

    Returns:
        A list of asyncpg.Record objects representing all users in the table.
        Returns an empty list if the query fails.
    """
    try:
        async with bot.pg_pool.acquire() as conn:
            rows = await conn.fetch(f"SELECT * FROM {TABLE_NAME}")
            return rows
    except Exception as e:
        pretty_log("error", f"Failed to fetch all {TABLE_NAME} rows: {e}", bot=bot)
        return []


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 💾 Fetch a single user row
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
async def fetch_user_captcha_alert(bot, user_id: int) -> asyncpg.Record | None:
    """
    Fetch a single user's captcha alert row by user_id.

    Args:
        bot: The Discord bot instance containing the PostgreSQL pool.
        user_id: The Discord user ID.

    Returns:
        An asyncpg.Record if the user exists, otherwise None.
    """
    try:
        async with bot.pg_pool.acquire() as conn:
            row = await conn.fetchrow(
                f"SELECT * FROM {TABLE_NAME} WHERE user_id=$1", user_id
            )
            return row
    except Exception as e:
        pretty_log(
            "error", f"Failed to fetch {TABLE_NAME} row for {user_id}: {e}", bot=bot
        )
        return None


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 💾 Upsert a user row
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
async def upsert_user_captcha_alert(bot, user_id: int, user_name: str, alert_type: str):
    """
    Insert a new captcha alert row or update an existing one for a user.

    Args:
        bot: The Discord bot instance containing the PostgreSQL pool.
        user_id: The Discord user ID.
        user_name: The Discord username.
        alert_type: Type of captcha alert to set.

    Notes:
        Also updates the in-memory cache via `upsert_user_captcha_alert_cache`.
    """
    try:
        from utils.cache.user_captcha_alert_cache import upsert_user_captcha_alert_cache

        async with bot.pg_pool.acquire() as conn:
            await conn.execute(
                f"""
                INSERT INTO {TABLE_NAME} (user_id, user_name, alert_type)
                VALUES ($1, $2, $3)
                ON CONFLICT (user_id)
                DO UPDATE SET user_name = EXCLUDED.user_name, alert_type = EXCLUDED.alert_type
                """,
                user_id,
                user_name,
                alert_type,
            )
            pretty_log(
                "db", f"Upserted captcha alert for {user_name} ({user_id})", bot=bot
            )
            upsert_user_captcha_alert_cache(
                user_id=user_id, user_name=user_name, alert_type=alert_type
            )
    except Exception as e:
        pretty_log(
            "error", f"Failed to upsert {TABLE_NAME} row for {user_id}: {e}", bot=bot
        )


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 💾 Remove a user row
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
async def remove_user_captcha_alert(bot, user_id: int):
    """
    Remove a user's captcha alert row from the database.

    Args:
        bot: The Discord bot instance containing the PostgreSQL pool.
        user_id: The Discord user ID.

    Notes:
        Also removes the user from the in-memory cache via `remove_user_captcha_alert_cache`.
    """
    try:
        from utils.cache.user_captcha_alert_cache import remove_user_captcha_alert_cache

        async with bot.pg_pool.acquire() as conn:
            await conn.execute(f"DELETE FROM {TABLE_NAME} WHERE user_id=$1", user_id)
            pretty_log("db", f"Removed captcha alert for user_id {user_id}", bot=bot)
            remove_user_captcha_alert_cache(user_id=user_id)

    except Exception as e:
        pretty_log(
            "error", f"Failed to remove {TABLE_NAME} row for {user_id}: {e}", bot=bot
        )


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 💾 Update alert_type for a user
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
async def update_alert_type(bot, user_id: int, new_alert_type: str):
    """
    Update the `alert_type` field for a given user in the database.

    Args:
        bot: The Discord bot instance containing the PostgreSQL pool.
        user_id: The Discord user ID.
        new_alert_type: The new alert type to set.

    Notes:
        Also updates the in-memory cache via `update_user_alert_type_cache`.
    """
    try:
        from utils.cache.user_captcha_alert_cache import update_user_alert_type_cache

        async with bot.pg_pool.acquire() as conn:
            await conn.execute(
                f"UPDATE {TABLE_NAME} SET alert_type=$1 WHERE user_id=$2",
                new_alert_type,
                user_id,
            )
            pretty_log(
                "db",
                f"Updated alert_type for user_id {user_id} → {new_alert_type}",
                bot=bot,
            )
            update_user_alert_type_cache(user_id=user_id, new_alert_type=new_alert_type)
    except Exception as e:
        pretty_log("error", f"Failed to update alert_type for {user_id}: {e}", bot=bot)
