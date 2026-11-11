import discord

from utils.loggers.pretty_logs import pretty_log

# SQL SCRIPT
"""CREATE TABLE pokemeow_timers (
    user_id BIGINT NOT NULL,
    user_name TEXT NOT NULL,
    timer_type TEXT NOT NULL,
    channel_id BIGINT NOT NULL,
    channel_name TEXT NOT NULL,
    remind_on BIGINT NOT NULL,

    PRIMARY KEY (user_id, timer_type)
);"""

async def upsert_pokemeow_timer(
    bot: discord.Client,
    user_id: int,
    user_name: str,
    timer_type: str,
    channel_id: int,
    channel_name: str,
    remind_on: int,
):
    """Upserts a pokemeow timer into the database."""
    query = """
    INSERT INTO pokemeow_timers (user_id, user_name, timer_type, channel_id, channel_name, remind_on)
    VALUES ($1, $2, $3, $4, $5, $6)
    ON CONFLICT (user_id, timer_type)
    DO UPDATE SET user_name = EXCLUDED.user_name,
                  channel_id = EXCLUDED.channel_id,
                  channel_name = EXCLUDED.channel_name,
                  remind_on = EXCLUDED.remind_on;
    """
    try:
        async with bot.pg_pool.acquire() as conn:
            await conn.execute(query, user_id, user_name, timer_type, channel_id, channel_name, remind_on)
    except Exception as e:
        pretty_log("error", f"Failed to upsert pokemeow timer for user {user_id}: {e}")


async def fetch_timer_due(bot:discord.Client, user_id: int, timer_type: str):
    """Fetches the pokemeow timer that is due for the given user and timer type."""
    query = """
    SELECT * FROM pokemeow_timers
    WHERE user_id = $1 AND timer_type = $2 AND remind_on <= EXTRACT(EPOCH FROM NOW())::BIGINT
    LIMIT 1
    """
    try:
        async with bot.pg_pool.acquire() as conn:
            row = await conn.fetchrow(query, user_id, timer_type)
        return row
    except Exception as e:
        pretty_log("error", f"Failed to fetch reminder due for user {user_id} and timer type {timer_type}: {e}")
        return None

async def fetch_timer(bot: discord.Client, user_id: int, timer_type: str):
    """Fetches the pokemeow timer for the given user and timer type, regardless of whether it is due."""
    query = """
    SELECT * FROM pokemeow_timers
    WHERE user_id = $1 AND timer_type = $2
    LIMIT 1
    """
    try:
        async with bot.pg_pool.acquire() as conn:
            row = await conn.fetchrow(query, user_id, timer_type)
        return row
    except Exception as e:
        pretty_log("error", f"Failed to fetch timer for user {user_id} and timer type {timer_type}: {e}")
        return None

async def remove_pokemeow_timer(bot: discord.Client, user_id: int, timer_type: str):
    """Removes the pokemeow timer for the given user and timer type."""
    query = """
    DELETE FROM pokemeow_timers
    WHERE user_id = $1 AND timer_type = $2
    """
    try:
        async with bot.pg_pool.acquire() as conn:
            await conn.execute(query, user_id, timer_type)
    except Exception as e:
        pretty_log("error", f"Failed to remove pokemeow timer for user {user_id} and timer type {timer_type}: {e}")


async def fetch_all_due_timers(bot: discord.Client):
    """
    Fetch special battle timers that are due now or earlier.
    Uses UNIX timestamp (seconds) for comparison.
    Returns a list of records ordered by ends_on ascending.
    """
    query = """
    SELECT * FROM pokemeow_timers
    WHERE remind_on <= EXTRACT(EPOCH FROM NOW())::BIGINT
    ORDER BY remind_on ASC
    """
    try:
        async with bot.pg_pool.acquire() as conn:
            rows = await conn.fetch(query)
        return rows
    except Exception as e:
        pretty_log("error", f"Failed to fetch all due timers: {e}")
        return []
