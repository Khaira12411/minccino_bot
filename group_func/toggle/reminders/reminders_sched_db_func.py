from typing import List, Optional
from datetime import datetime, timedelta
from utils.loggers.pretty_logs import pretty_log

# ────────────────────────────────────────────
#     🐱 Pokemeow Reminders Schedule DB 🐱
# ────────────────────────────────────────────

async def fetch_all_schedules(bot) -> list[dict]:
    try:
        async with bot.pg_pool.acquire() as conn:
            rows = await conn.fetch(
                """
                SELECT reminder_id, user_id, user_name, type, ends_on, remind_next_on, reminder_sent
                FROM pokemeow_reminders_schedule
                """
            )
            return [dict(row) for row in rows]
    except Exception as e:
        pretty_log("error", f"Failed to fetch all schedules: {e}", bot=bot)
        return []


async def fetch_user_schedule(bot, user_id: int, type_: str) -> Optional[dict]:
    try:
        async with bot.pg_pool.acquire() as conn:
            row = await conn.fetchrow(
                """
                SELECT reminder_id, user_id, user_name, type, ends_on, remind_next_on, reminder_sent
                FROM pokemeow_reminders_schedule
                WHERE user_id=$1 AND type=$2
                """,
                user_id,
                type_,
            )
            return dict(row) if row else None
    except Exception as e:
        pretty_log(
            "error",
            f"Failed to fetch schedule for user {user_id}, type {type_}: {e}",
            bot=bot,
        )
        return None
# ────────────────────────────────────────────
#   🐱 Fetch User Reminder Rows
# ────────────────────────────────────────────
async def fetch_user_schedules(bot, user_id: int) -> List[dict]:
    """
    Fetch all reminder rows for a given user_id.
    Returns a list of dicts.
    """
    try:
        async with bot.pg_pool.acquire() as conn:
            rows = await conn.fetch(
                """
                SELECT reminder_id, user_id, user_name, type, ends_on, remind_next_on, reminder_sent
                FROM pokemeow_reminders_schedule
                WHERE user_id = $1
                """,
                user_id,
            )
            return [dict(row) for row in rows]
    except Exception as e:
        pretty_log(
            "error", f"Failed to fetch schedules for user {user_id}: {e}", bot=bot
        )
        return []


async def upsert_user_schedule(
    bot,
    user_id: int,
    user_name: str,
    type_: str,
    ends_on: int,
    remind_next_on: Optional[int] = None,
    reminder_sent: bool = False,  # new param
):
    try:
        async with bot.pg_pool.acquire() as conn:
            await conn.execute(
                """
                INSERT INTO pokemeow_reminders_schedule (user_id, user_name, type, ends_on, remind_next_on, reminder_sent)
                VALUES ($1, $2, $3, $4, $5, $6)
                ON CONFLICT (user_id, type) DO UPDATE
                SET user_name = EXCLUDED.user_name,
                    ends_on = EXCLUDED.ends_on,
                    remind_next_on = EXCLUDED.remind_next_on,
                    reminder_sent = EXCLUDED.reminder_sent
                """,
                user_id,
                user_name,
                type_,
                ends_on,
                remind_next_on,
                reminder_sent,
            )
        pretty_log(
            "info", f"Upserted schedule for user {user_id}, type {type_}", bot=bot
        )
    except Exception as e:
        pretty_log(
            "error",
            f"Failed to upsert schedule for user {user_id}, type {type_}: {e}",
            bot=bot,
        )


async def delete_user_schedule(bot, user_id: int, type_: str):
    """
    Delete a user's schedule row by type.
    """
    try:
        async with bot.pg_pool.acquire() as conn:
            await conn.execute(
                "DELETE FROM pokemeow_reminders_schedule WHERE user_id=$1 AND type=$2",
                user_id,
                type_,
            )
        pretty_log(
            "info", f"Deleted schedule for user {user_id}, type {type_}", bot=bot
        )
    except Exception as e:
        pretty_log(
            "error",
            f"Failed to delete schedule for user {user_id}, type {type_}: {e}",
            bot=bot,
        )


# ────────────────────────────────────────────
# Catchbot-specific helpers
# ────────────────────────────────────────────


async def get_catchbot_reminds_next_on(bot, user_id: int) -> Optional[dict]:
    """
    Fetch the `remind_next_on`, `reminder_id`, and `reminder_sent` for a user's catchbot reminder.
    """
    row = await fetch_user_schedule(bot, user_id, "catchbot")
    if row:
        return {
            "remind_next_on": row.get("remind_next_on"),
            "reminder_id": row.get("reminder_id"),
            "reminder_sent": row.get("reminder_sent", False),
        }
    return None


async def update_catchbot_reminds_next_on(
    bot, user_id: int, minutes: int | None, ends_on: int | None = None
):
    try:
        if not minutes or minutes <= 0 or not ends_on:
            next_on = None
        else:
            next_on = calculate_remind_next_on(
                {"repeating": minutes, "mode": "dms"}, ends_on
            )

        async with bot.pg_pool.acquire() as conn:
            await conn.execute(
                """
                UPDATE pokemeow_reminders_schedule
                SET remind_next_on = $1
                WHERE user_id = $2 AND type = 'catchbot'
                """,
                next_on,
                user_id,
            )

        pretty_log(
            "info",
            f"Updated catchbot remind_next_on for user {user_id} -> {next_on}",
            bot=bot,
        )
    except Exception as e:
        pretty_log(
            "error",
            f"Failed to update catchbot remind_next_on for user {user_id}: {e}",
            bot=bot,
        )


def calculate_remind_next_on(user_settings: dict, ends_on: int) -> Optional[int]:
    """
    Calculate the remind_next_on timestamp for a user.
    """
    mode = user_settings.get("mode", "off")
    if mode == "off":
        return None

    repeating = user_settings.get("repeating")
    if not repeating:
        return None

    return ends_on + int(repeating) * 60  # convert minutes to seconds


async def mark_reminder_sent(bot, reminder_id: int):
    query = "UPDATE pokemeow_reminders_schedule SET reminder_sent = TRUE WHERE reminder_id = $1"
    async with bot.pg_pool.acquire() as conn:
        await conn.execute(query, reminder_id)


# 🗑️ Delete reminder by ID
async def delete_reminder(bot, reminder_id: int):
    try:
        async with bot.pg_pool.acquire() as conn:
            await conn.execute(
                "DELETE FROM pokemeow_reminders_schedule WHERE reminder_id = $1",
                reminder_id,
            )
        pretty_log("db", f"Deleted reminder {reminder_id}", bot=bot)
    except Exception as e:
        pretty_log("error", f"Failed to delete reminder {reminder_id}: {e}", bot=bot)
