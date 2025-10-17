import asyncpg
from utils.loggers.pretty_logs import pretty_log


# Add or update a special battle timer (upsert)
async def upsert_special_battle_timer(
    bot, user_id: int, user_name: str, npc_name: str, ends_on: int, channel_id: int
):
    try:
        async with bot.pg_pool.acquire() as conn:
            await conn.execute(
                """
                INSERT INTO special_battle_timers (user_id, user_name, npc_name, ends_on, channel_id)
                VALUES ($1, $2, $3, $4, $5)
                ON CONFLICT (user_id, npc_name)
                DO UPDATE SET user_name = $2, ends_on = $4, channel_id = $5
                """,
                user_id,
                user_name,
                npc_name,
                ends_on,
                channel_id,
            )
            pretty_log(
                "info",
                f"Upserted special battle timer for {user_name}, npc {npc_name}, ends_on {ends_on}",
            )
    except Exception as e:
        pretty_log(
            "warn",
            f"Failed to upsert special battle timer for user {user_id}, npc {npc_name}: {e}",
        )


# Get a special battle timer for a user and npc
async def get_special_battle_timer(bot, user_id: int, npc_name: str):
    try:
        async with bot.pg_pool.acquire() as conn:
            row = await conn.fetchrow(
                "SELECT * FROM special_battle_timers WHERE user_id = $1 AND npc_name = $2",
                user_id,
                npc_name,
            )
            return dict(row) if row else None
    except Exception as e:
        pretty_log(
            "warn",
            f"Failed to fetch special battle timer for user {user_id}, npc {npc_name}: {e}",
        )
        return None


# Remove a special battle timer
async def remove_special_battle_timer(bot, user_id: int, npc_name: str):
    try:
        async with bot.pg_pool.acquire() as conn:
            await conn.execute(
                "DELETE FROM special_battle_timers WHERE user_id = $1 AND npc_name = $2",
                user_id,
                npc_name,
            )
    except Exception as e:
        pretty_log(
            "warn",
            f"Failed to remove special battle timer for user {user_id}, npc {npc_name}: {e}",
        )


# Get all special battle timers for a user
async def get_all_special_battle_timers_for_user(bot, user_id: int):
    try:
        async with bot.pg_pool.acquire() as conn:
            rows = await conn.fetch(
                "SELECT * FROM special_battle_timers WHERE user_id = $1", user_id
            )
            return [dict(row) for row in rows]
    except Exception as e:
        pretty_log(
            "warn", f"Failed to fetch all special battle timers for user {user_id}: {e}"
        )
        return []


# Clear expired timers
async def clear_expired_special_battle_timers(bot, current_unix: int):
    try:
        async with bot.pg_pool.acquire() as conn:
            await conn.execute(
                "DELETE FROM special_battle_timers WHERE ends_on <= $1", current_unix
            )
    except Exception as e:
        pretty_log("warn", f"Failed to clear expired special battle timers: {e}")


# 💙─────────────────────────────────────────────💙
#       ⏰ Fetch Due Special Battle Timers
# 💙─────────────────────────────────────────────💙
async def fetch_due_special_battle_timers(bot):
    """
    Fetch special battle timers that are due now or earlier.
    Uses UNIX timestamp (seconds) for comparison.
    Returns a list of records ordered by ends_on ascending.
    """
    try:
        async with bot.pg_pool.acquire() as conn:
            rows = await conn.fetch(
                """
                SELECT *
                FROM special_battle_timers
                WHERE ends_on <= EXTRACT(EPOCH FROM NOW())::BIGINT
                ORDER BY ends_on ASC;
                """
            )
            return [dict(row) for row in rows]
    except Exception as e:
        pretty_log("warn", f"Failed to fetch due special battle timers: {e}")
        return []
