from time import time

import discord

from utils.loggers.pretty_logs import pretty_log

# SQL SCRIPT
"""CREATE TABLE misc_pokemeow_reminders (
    user_id BIGINT NOT NULL,
    type VARCHAR(50) NOT NULL,
    user_name VARCHAR(100) NOT NULL,
    remind_on BIGINT NOT NULL,
    PRIMARY KEY (user_id, type, remind_on)
);
"""


# 🐱 Upsert Secret Santa Reminder for 4 hours
async def upsert_secret_santa_reminder(
    bot, user_id: int, user_name: str, channel_id: int
):
    type = "secret_santa"
    remind_on = int(time()) + 4 * 60 * 60  # 4 hours from now
    try:
        async with bot.pg_pool.acquire() as conn:
            await conn.execute(
                """
                INSERT INTO misc_pokemeow_reminders (user_id, type, user_name, remind_on, channel_id)
                VALUES ($1, $2, $3, $4, $5)
                ON CONFLICT (user_id, type, remind_on)
                DO UPDATE SET user_name = EXCLUDED.user_name, remind_on = EXCLUDED.remind_on, channel_id = EXCLUDED.channel_id
                """,
                user_id,
                type,
                user_name,
                remind_on,
                channel_id,
            )
            pretty_log(
                "info",
                f"Upserted secret santa reminder for {user_name}, reminds on {remind_on}, channel {channel_id}",
            )
    except Exception as e:
        pretty_log(
            "warn",
            f"Failed to upsert secret santa reminder for user {user_id}: {e}",
        )


# 🐱 Remove secret santa reminder
async def remove_secret_santa_reminder(bot, user_id: int):
    type = "secret_santa"
    try:
        async with bot.pg_pool.acquire() as conn:
            await conn.execute(
                "DELETE FROM misc_pokemeow_reminders WHERE user_id = $1 AND type = $2",
                user_id,
                type,
            )
            pretty_log(
                "info",
                f"Removed secret santa reminder for user {user_id}",
            )
    except Exception as e:
        pretty_log(
            "warn",
            f"Failed to remove secret santa reminder for user {user_id}: {e}",
        )


# 🐱 Fetch all due secret santa reminders
async def fetch_due_secret_santa_reminders(bot):
    """
    Fetch secret santa reminders that are due now or earlier.
    Uses UNIX timestamp (seconds) for comparison.
    Returns a list of records ordered by remind_on ascending.
    """
    type = "secret_santa"
    try:
        async with bot.pg_pool.acquire() as conn:
            rows = await conn.fetch(
                """
                SELECT *
                FROM misc_pokemeow_reminders
                WHERE type = $1 AND remind_on <= EXTRACT(EPOCH FROM NOW())::BIGINT
                ORDER BY remind_on ASC;
                """,
                type,
            )
            return [dict(row) for row in rows]
    except Exception as e:
        pretty_log("warn", f"Failed to fetch due secret santa reminders: {e}")
        return []
