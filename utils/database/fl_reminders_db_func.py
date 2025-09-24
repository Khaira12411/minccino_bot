# utils/database/fl_reminder_db_func.py

import discord
from utils.loggers.pretty_logs import pretty_log


# 🍭 Get a registered personal channel
async def get_registered_personal_channel(
    bot: discord.Client, user_id: int
) -> int | None:
    try:
        async with bot.pg_pool.acquire() as conn:
            row = await conn.fetchrow(
                "SELECT channel_id FROM personal_channels WHERE user_id = $1", user_id
            )
            return row["channel_id"] if row else None
    except Exception as e:
        pretty_log("warn", f"Failed to fetch personal channel for user {user_id}: {e}")
        return None

# 🟣────────────────────────────────────────────
#   Upsert a reminder row (with defaults)
# ─────────────────────────────────────────────
async def upsert_fl_reminder_db(
    bot,
    user_id: int,
    user_name: str,
    reminder_type: str | None = None,
    channel_id: int | None = None,
):
    try:
        # Default reminder_type to "channel"
        reminder_type = reminder_type or "channel"

        # If reminder_type is channel but channel_id not provided, fetch it
        if reminder_type == "channel" and channel_id is None:
            channel_id = await get_registered_personal_channel(bot, user_id)

        async with bot.pg_pool.acquire() as conn:
            await conn.execute(
                """
                INSERT INTO feeling_lucky_reminders (user_id, user_name, reminder_type, channel_id)
                VALUES ($1, $2, $3, $4)
                ON CONFLICT (user_id)
                DO UPDATE SET
                    user_name = EXCLUDED.user_name,
                    reminder_type = EXCLUDED.reminder_type,
                    channel_id = EXCLUDED.channel_id
                """,
                user_id,
                user_name,
                reminder_type,
                channel_id,
            )
    except Exception as e:
        pretty_log(
            "error",
            f"Failed to upsert FL reminder for {user_id}: {e}",
            bot=bot,
        )


# 🟣────────────────────────────────────────────
#   Update only the reminder_type for a user
# ─────────────────────────────────────────────
async def update_fl_reminder_type(bot, user_id: int, reminder_type: str):
    """
    Update the reminder_type for a given user in the FL reminders table.
    Leaves user_name and channel_id unchanged.
    """
    try:
        async with bot.pg_pool.acquire() as conn:
            await conn.execute(
                """
                UPDATE feeling_lucky_reminders
                SET reminder_type = $2
                WHERE user_id = $1
                """,
                user_id,
                reminder_type,
            )
    except Exception as e:
        pretty_log(
            "error",
            f"Failed to update reminder_type for FL user {user_id}: {e}",
            bot=bot,
        )

# 🟣────────────────────────────────────────────
#   Fetch a single reminder row
# ─────────────────────────────────────────────
async def fetch_fl_reminder_db(bot, user_id: int) -> dict | None:
    try:
        async with bot.pg_pool.acquire() as conn:
            row = await conn.fetchrow(
                "SELECT * FROM feeling_lucky_reminders WHERE user_id = $1", user_id
            )
            return dict(row) if row else None
    except Exception as e:
        pretty_log(
            "error",
            f"Failed to fetch FL reminder for {user_id}: {e}",
            bot=bot,
        )
        return None


# 🟣────────────────────────────────────────────
#   Fetch all reminder rows
# ─────────────────────────────────────────────
async def fetch_all_fl_reminders_db(bot) -> list[dict]:
    try:
        async with bot.pg_pool.acquire() as conn:
            rows = await conn.fetch("SELECT * FROM feeling_lucky_reminders")
            return [dict(row) for row in rows]
    except Exception as e:
        pretty_log(
            "error",
            f"Failed to fetch all FL reminders: {e}",
            bot=bot,
        )
        return []


# 🟣────────────────────────────────────────────
#   Remove a reminder row
# ─────────────────────────────────────────────
async def remove_fl_reminder_db(bot, user_id: int):
    try:
        async with bot.pg_pool.acquire() as conn:
            await conn.execute(
                "DELETE FROM feeling_lucky_reminders WHERE user_id = $1", user_id
            )
    except Exception as e:
        pretty_log(
            "error",
            f"Failed to remove FL reminder for {user_id}: {e}",
            bot=bot,
        )
