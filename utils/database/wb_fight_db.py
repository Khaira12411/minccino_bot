import asyncpg
import discord

from utils.loggers.pretty_logs import pretty_log

TABLE_NAME = "user_alerts"
ALERT_TYPE = "wb_battle"


async def upsert_user_wb_battle_alert(
    bot: discord.Client,
    user: discord.Member,
    notify: str,
):
    user_id = user.id
    user_name = user.name
    try:
        async with bot.pg_pool.acquire() as conn:
            await conn.execute(
                f"""
                INSERT INTO {TABLE_NAME} (user_id, user_name, alert_type, notify)
                VALUES ($1, $2, $3, $4)
                ON CONFLICT (user_id, alert_type)
                DO UPDATE SET user_name = $2, notify = $4
                """,
                user_id,
                user_name,
                ALERT_TYPE,
                notify,
            )
            pretty_log(
                "db",
                f"Upserted {ALERT_TYPE} alert for {user_name} → notify: {notify}",
                bot=bot,
            )
            # Upsert into cache as well
            from utils.cache.wb_battle_alert_cache import upsert_wb_battle_alert_cache
            upsert_wb_battle_alert_cache(user_id, user_name, notify)

    except Exception as e:
        pretty_log(
            "error", f"Failed to upsert {ALERT_TYPE} alert for {user_id}: {e}", bot=bot
        )


async def remove_user_wb_battle_alert(bot: discord.Client, user: discord.Member):
    """
    Remove a user's world boss battle alert row from DB.

    Args:
        bot: The Discord bot instance containing the PostgreSQL pool
        user: The Discord member object.
    """
    user_id = user.id
    user_name = user.name

    try:
        async with bot.pg_pool.acquire() as conn:
            await conn.execute(
                f"DELETE FROM {TABLE_NAME} WHERE user_id=$1 AND alert_type=$2",
                user_id,
                ALERT_TYPE,
            )
        pretty_log(
            "db",
            f"Removed {ALERT_TYPE} alert for {user_name}",
            bot=bot,
        )
        # Remove from cache as well
        from utils.cache.wb_battle_alert_cache import remove_wb_battle_alert_cache
        remove_wb_battle_alert_cache(user_id)

    except Exception as e:
        pretty_log(
            "error", f"Failed to remove {ALERT_TYPE} alert for {user_id}: {e}", bot=bot
        )


# Update user wb battle alert notify
async def update_user_wb_battle_alert_notify(
    bot: discord.Client, user: discord.Member, notify: str
):
    """
    Update a user's world boss battle alert notify setting in DB.

    Args:
        bot: The Discord bot instance containing the PostgreSQL pool.
        user: The Discord member object.
        notify: The new notify setting.
    """
    user_id = user.id
    user_name = user.name

    try:
        async with bot.pg_pool.acquire() as conn:
            await conn.execute(
                f"""
                UPDATE {TABLE_NAME}
                SET notify = $1, user_name = $2
                WHERE user_id = $3 AND alert_type = $4
                """,
                notify,
                user_name,
                user_id,
                ALERT_TYPE,
            )
        pretty_log(
            "db",
            f"Updated {ALERT_TYPE} alert notify for {user_name} → notify: {notify}",
            bot=bot,
        )
        # Update cache as well
        from utils.cache.wb_battle_alert_cache import update_wb_battle_alert_cache
        update_wb_battle_alert_cache(user_id, notify)

    except Exception as e:
        pretty_log(
            "error",
            f"Failed to update {ALERT_TYPE} alert notify for {user_id}: {e}",
            bot=bot,
        )

async def fetch_user_wb_battle_alert(bot: discord.Client, user_id: int):
    """
    Fetch a user's world boss battle alert settings from DB.

    Args:
        bot: The Discord bot instance containing the PostgreSQL pool.
        user_id: The Discord user ID.

    Returns:
        A dictionary containing the alert settings, or None if not found.
    """
    try:
        async with bot.pg_pool.acquire() as conn:
            row = await conn.fetchrow(
                f"""
                SELECT * FROM {TABLE_NAME}
                WHERE user_id = $1 AND alert_type = $2
                """,
                user_id,
                ALERT_TYPE,
            )
            return dict(row) if row else None

    except Exception as e:
        pretty_log(
            "error",
            f"Failed to fetch {ALERT_TYPE} alert for {user_id}: {e}",
            bot=bot,
        )
        return None

async def fetch_all_wb_battle_alerts(bot: discord.Client):
    """
    Fetch all world boss battle alerts from DB.

    Args:
        bot: The Discord bot instance containing the PostgreSQL pool.
    Returns:
        A list of dictionaries containing all alert settings.
    """
    try:
        async with bot.pg_pool.acquire() as conn:
            rows = await conn.fetch(
                f"""
                SELECT * FROM {TABLE_NAME}
                WHERE alert_type = $1
                """,
                ALERT_TYPE,
            )
            return [dict(row) for row in rows]

    except Exception as e:
        pretty_log(
            "error",
            f"Failed to fetch all {ALERT_TYPE} alerts: {e}",
            bot=bot,
        )
        return []

# Upsert wb battle reminder
async def upsert_wb_battle_reminder(
    bot: discord.Client,
    user_id: int,
    user_name: str,
    wb_name: str,
    channel_id: int,
    remind_on: int,
):
    """
    Upsert a world boss battle reminder for a user.
    """
    query = """
    INSERT INTO wb_battle_reminders (user_id, user_name, wb_name, channel_id, remind_on)
    VALUES ($1, $2, $3, $4, $5)
    ON CONFLICT (user_id, wb_name)
    DO UPDATE SET
        user_name = EXCLUDED.user_name,
        channel_id = EXCLUDED.channel_id,
        remind_on = EXCLUDED.remind_on;
    """
    try:
        async with bot.pg_pool.acquire() as conn:
            await conn.execute(
                query,
                user_id,
                user_name,
                wb_name,
                channel_id,
                remind_on,
            )
        pretty_log(
            "db",
            f"Upserted WB battle reminder for user {user_name} ({wb_name})",
        )

    except Exception as e:
        pretty_log(
            "error",
            f"Failed to upsert WB battle reminder for user {user_id} ({wb_name}): {e}",
            bot=bot,
        )


# Fetch user reminder for wb
async def fetch_wb_battle_reminder(bot: discord.Client, user_id: int, wb_name: str):
    """
    Fetch a world boss battle reminder for a user.
    """
    query = """
    SELECT * FROM wb_battle_reminders
    WHERE user_id = $1 AND wb_name = $2;
    """
    try:
        async with bot.pg_pool.acquire() as conn:
            row = await conn.fetchrow(query, user_id, wb_name)
            return dict(row) if row else None
    except Exception as e:
        pretty_log(
            "error",
            f"Failed to fetch WB battle reminder for user {user_id} ({wb_name}): {e}",
            bot=bot,
        )
        return None


# Fetch all due reminders for world boss battles
async def fetch_due_wb_battle_reminders(bot: discord.Client):
    """
    Fetch all world boss battle reminders that are due.
    """
    query = """
    SELECT user_id, user_name, wb_name, channel_id, remind_on
    FROM wb_battle_reminders
    WHERE remind_on <= EXTRACT(EPOCH FROM NOW())::BIGINT;
    """
    try:
        async with bot.pg_pool.acquire() as conn:
            rows = await conn.fetch(query)
            return [dict(row) for row in rows]
    except Exception as e:
        pretty_log(
            "error",
            f"Failed to fetch due WB battle reminders: {e}",
            bot=bot,
        )
        return []


# Delete a world boss battle reminder
async def remove_wb_reminder(bot: discord.Client, user_id: int):
    """
    Remove a world boss battle reminder for a user.
    """
    query = "DELETE FROM wb_battle_reminders WHERE user_id = $1;"
    try:
        async with bot.pg_pool.acquire() as conn:
            await conn.execute(query, user_id)
        pretty_log(
            "db",
            f"Removed WB battle reminder for user_id {user_id}",
            bot=bot,
        )
    except Exception as e:
        pretty_log(
            "error",
            f"Failed to remove WB battle reminder for user_id {user_id}: {e}",
            bot=bot,
        )
