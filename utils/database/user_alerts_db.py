import discord

from utils.loggers.pretty_logs import pretty_log

# SQL SCRIPT
"""CREATE TABLE user_alerts (
    user_id BIGINT NOT NULL,
    user_name TEXT NOT NULL,
    alert_type TEXT NOT NULL,
    notify TEXT NOT NULL,
    PRIMARY KEY (user_id, alert_type)
);"""


async def upsert_user_alert(
    bot,
    user_id: int,
    user_name: str,
    alert_type: str,
    notify: str,
):
    """Insert or update a user alert setting."""
    try:
        async with bot.pg_pool.acquire() as conn:
            await conn.execute(
                """
                INSERT INTO user_alerts (user_id, user_name, alert_type, notify)
                VALUES ($1, $2, $3, $4)
                ON CONFLICT (user_id, alert_type)
                DO UPDATE SET user_name = EXCLUDED.user_name, notify = EXCLUDED.notify
                """,
                user_id,
                user_name,
                alert_type,
                notify,
            )
        pretty_log(
            tag="db",
            message=f"Upserted alert setting for {user_name}, alert_type {alert_type} to notify={notify}",
            bot=bot,
        )
        # Update cache as well
        from utils.cache.user_alert_cache import upsert_user_alert_cache
        upsert_user_alert_cache(
            user_id=user_id,
            alert_type=alert_type,
            user_name=user_name,
            notify=notify,
        )

    except Exception as e:
        pretty_log(
            tag="error",
            message=f"Failed to upsert user alert setting: {e}",
            bot=bot,
        )


async def update_alert_notify(
    bot,
    user_id: int,
    alert_type: str,
    notify: str,
):
    """Update the notify setting for a user alert."""
    try:
        async with bot.pg_pool.acquire() as conn:
            await conn.execute(
                """
                UPDATE user_alerts
                SET notify = $1
                WHERE user_id = $2 AND alert_type = $3
                """,
                notify,
                user_id,
                alert_type,
            )
        pretty_log(
            tag="db",
            message=f"Updated notify to {notify} for user_id {user_id}, alert_type {alert_type}",
            bot=bot,
        )
        # Update cache as well
        from utils.cache.user_alert_cache import update_user_alert_notify_cache
        update_user_alert_notify_cache(
            user_id=user_id,
            alert_type=alert_type,
            notify=notify,
        )
    except Exception as e:
        pretty_log(
            tag="error",
            message=f"Failed to update user alert notify setting: {e}",
            bot=bot,
        )

async def fetch_user_alert_notify(
    bot,
    user_id: int,
    alert_type: str,
) -> str | None:
    """Fetch the notify setting for a user alert."""
    try:
        async with bot.pg_pool.acquire() as conn:
            row = await conn.fetchrow(
                """
                SELECT notify FROM user_alerts
                WHERE user_id = $1 AND alert_type = $2
                """,
                user_id,
                alert_type,
            )
            return row["notify"] if row else None
    except Exception as e:
        pretty_log(
            tag="error",
            message=f"Failed to fetch user alert notify setting: {e}",
            bot=bot,
        )
        return None

async def fetch_user_alert(bot, user_id: int, alert_type: str) -> dict | None:
    """Fetch a user alert setting."""
    try:
        async with bot.pg_pool.acquire() as conn:
            row = await conn.fetchrow(
                """
                SELECT * FROM user_alerts
                WHERE user_id = $1 AND alert_type = $2
                """,
                user_id,
                alert_type,
            )
            return dict(row) if row else None
    except Exception as e:
        pretty_log(
            tag="error",
            message=f"Failed to fetch user alert setting: {e}",
            bot=bot,
        )
        return None


async def fetch_all_user_alerts(bot) -> list[dict]:
    """Fetch all user alert settings."""
    try:
        async with bot.pg_pool.acquire() as conn:
            rows = await conn.fetch("SELECT * FROM user_alerts")
            return [dict(row) for row in rows]
    except Exception as e:
        pretty_log(
            tag="error",
            message=f"Failed to fetch all user alert settings: {e}",
            bot=bot,
        )
        return []

async def remove_user_alerts_for_user(bot, user_id: int):
    """Remove all alert settings for a specific user."""
    try:
        async with bot.pg_pool.acquire() as conn:
            await conn.execute(
                """
                DELETE FROM user_alerts
                WHERE user_id = $1
                """,
                user_id,
            )
        pretty_log(
            tag="db",
            message=f"Removed all alert settings for user_id {user_id}",
            bot=bot,
        )
        # Update cache as well
        from utils.cache.user_alert_cache import remove_user_alerts_for_user_cache
        remove_user_alerts_for_user_cache(user_id=user_id)
    except Exception as e:
        pretty_log(
            tag="error",
            message=f"Failed to remove user alert settings for user_id {user_id}: {e}",
            bot=bot,
        )

async def delete_user_alert(bot, user_id: int, alert_type: str):
    """Delete a user alert setting."""
    try:
        async with bot.pg_pool.acquire() as conn:
            await conn.execute(
                """
                DELETE FROM user_alerts
                WHERE user_id = $1 AND alert_type = $2
                """,
                user_id,
                alert_type,
            )
        pretty_log(
            tag="db",
            message=f"Deleted alert setting for user_id {user_id}, alert_type {alert_type}",
            bot=bot,
        )
        # Update cache as well
        from utils.cache.user_alert_cache import delete_user_alert_cache
        delete_user_alert_cache(
            user_id=user_id,
            alert_type=alert_type,
        )
    except Exception as e:
        pretty_log(
            tag="error",
            message=f"Failed to delete user alert setting: {e}",
            bot=bot,
        )
