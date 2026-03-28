import discord

from utils.loggers.pretty_logs import pretty_log

# SQL TABLE
"""CREATE TABLE berry_reminder (
    user_id BIGINT,
    user_name TEXT,
    slot_number INT,
    remind_on BIGINT,
    stage TEXT,
    channel_id BIGINT,
    channel_name TEXT,
    berry_name TEXT,
    PRIMARY KEY (user_id, slot_number)
);"""


async def upsert_berry_reminder(
    bot: discord.Client,
    user_id: int,
    user_name: str,
    slot_number: int,
    remind_on: int,
    stage: str,
    channel_id: int,
    channel_name: str,
    berry_name: str,
):
    """Upserts a berry reminder for the given user_id and slot_number."""
    try:
        async with bot.pg_pool.acquire() as conn:
            await conn.execute(
                """
                INSERT INTO berry_reminder (user_id, user_name, slot_number, remind_on, stage, channel_id, channel_name, berry_name)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
                ON CONFLICT (user_id, slot_number) DO UPDATE SET
                    user_name = EXCLUDED.user_name,
                    remind_on = EXCLUDED.remind_on,
                    stage = EXCLUDED.stage,
                    channel_id = EXCLUDED.channel_id,
                    channel_name = EXCLUDED.channel_name,
                    berry_name = EXCLUDED.berry_name
                """,
                user_id,
                user_name,
                slot_number,
                remind_on,
                stage,
                channel_id,
                channel_name,
                berry_name,
            )
        pretty_log(
            "db",
            f"Upserted berry reminder for {user_name} (user_id: {user_id}) in slot {slot_number}, reminds on {remind_on}, stage: {stage}",
        )
    except Exception as e:
        pretty_log(
            "warn",
            f"Failed to upsert berry reminder for user {user_id} in slot {slot_number}: {e}",
        )


async def fetch_user_all_berry_reminder(bot: discord.Client, user_id: int):
    """
    Fetches all berry reminders for the given user_id.
    Returns a list of dictionaries with keys: user_id, user_name, slot_number, remind_on, stage, channel_id, channel_name, berry_name.
    """
    try:
        async with bot.pg_pool.acquire() as conn:
            rows = await conn.fetch(
                """
                SELECT user_id, user_name, slot_number, remind_on, stage, channel_id, channel_name, berry_name
                FROM berry_reminder
                WHERE user_id = $1
                ORDER BY slot_number ASC;
                """,
                user_id,
            )
            return [dict(row) for row in rows]
    except Exception as e:
        pretty_log("warn", f"Failed to fetch berry reminders for user {user_id}: {e}")
        return []


async def remove_berry_reminder(
    bot: discord.Client,
    user_id: int,
    slot_number: int,
):
    """
    Removes a berry reminder for the given user_id and slot_number.
    """
    async with bot.pg_pool.acquire() as conn:
        await conn.execute(
            """
            DELETE FROM berry_reminder
            WHERE user_id = $1 AND slot_number = $2
            """,
            user_id,
            slot_number,
        )
    pretty_log(
        "db",
        f"Removed berry reminder for user_id {user_id} in slot {slot_number}",
    )


async def fetch_all_due_berry_reminders(bot: discord.Client):
    """
    Fetches all berry reminders that are due within the next minute (remind_on <= now + 60s).
    Returns a list of dictionaries with all columns from the berry_reminder table.
    """
    try:
        async with bot.pg_pool.acquire() as conn:
            rows = await conn.fetch(
                """
                SELECT DISTINCT ON (user_id, slot_number) *
                FROM berry_reminder
                WHERE remind_on <= (EXTRACT(EPOCH FROM NOW())::BIGINT + 60)
                ORDER BY user_id, slot_number, remind_on ASC;
                """
            )

            return [dict(row) for row in rows]
    except Exception as e:
        pretty_log("warn", f"Failed to fetch due berry reminders: {e}")
        return []
