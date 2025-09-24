# 🌟────────────────────────────────────────────
#   DB Functions: Feeling Lucky Cooldowns
# 🌟────────────────────────────────────────────

import time

import asyncpg

from utils.loggers.pretty_logs import pretty_log

# ⛄ Upsert cooldown row (6 hours from now)
async def upsert_feeling_lucky_cd(bot, user_id: int, user_name: str):
    from utils.cache.fl_cache import upsert_feeling_lucky_cache

    # Calculate cooldown: now + 6 hours (6 * 3600 seconds)
    cooldown_until = int(time.time()) + 6 * 3600

    try:
        async with bot.pg_pool.acquire() as conn:
            await conn.execute(
                """
                INSERT INTO feeling_lucky_cd (user_id, user_name, cooldown_until)
                VALUES ($1, $2, $3)
                ON CONFLICT (user_id)
                DO UPDATE SET
                    user_name = EXCLUDED.user_name,
                    cooldown_until = EXCLUDED.cooldown_until
                """,
                user_id,
                user_name,
                cooldown_until,
            )
        upsert_feeling_lucky_cache(
            user_id=user_id, user_name=user_name, cooldown_until=cooldown_until
        )
    except Exception as e:
        pretty_log(
            "error",
            f"Failed to upsert feeling_lucky_cd for {user_id}: {e}",
            bot=bot,
        )


# ⛄ Fetch single row
async def fetch_feeling_lucky_cd(bot, user_id: int) -> asyncpg.Record | None:
    try:
        async with bot.pg_pool.acquire() as conn:
            row = await conn.fetchrow(
                """
                SELECT * FROM feeling_lucky_cd
                WHERE user_id = $1
                """,
                user_id,
            )
            return row
    except Exception as e:
        pretty_log(
            "error",
            f"Failed to fetch feeling_lucky_cd for {user_id}: {e}",
            bot=bot,
        )
        return None


# ⛄ Fetch all rows
async def fetch_all_feeling_lucky_cd(bot) -> list[asyncpg.Record]:
    try:
        async with bot.pg_pool.acquire() as conn:
            rows = await conn.fetch("SELECT * FROM feeling_lucky_cd")
            return rows
    except Exception as e:
        pretty_log(
            "error",
            f"Failed to fetch all feeling_lucky_cd rows: {e}",
            bot=bot,
        )
        return []

# ⛄ Remove row
async def remove_feeling_lucky_cd(bot, user_id: int):
    try:
        async with bot.pg_pool.acquire() as conn:
            await conn.execute(
                """
                DELETE FROM feeling_lucky_cd
                WHERE user_id = $1
                """,
                user_id,
            )
        from utils.cache.fl_cache import remove_feeling_lucky_cache

        remove_feeling_lucky_cache(user_id=user_id)
    except Exception as e:
        pretty_log(
            "error",
            f"Failed to remove feeling_lucky_cd for {user_id}: {e}",
            bot=bot,
        )
