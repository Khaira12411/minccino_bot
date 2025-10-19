from utils.loggers.pretty_logs import pretty_log


# Add or update a place's score (upsert)
async def upsert_halloween_con_top(bot, place: str, score: int):
    try:
        async with bot.pg_pool.acquire() as conn:
            await conn.execute(
                """
                INSERT INTO halloween_con_top (place, score)
                VALUES ($1, $2)
                ON CONFLICT (place)
                DO UPDATE SET score = $2
                """,
                place,
                score,
            )
            from utils.cache.halloween_con_top_cache import (
                upsert_halloween_con_top_cache,
            )

            # upsert in cache too
            pretty_log(
                "db",
                f"Upserted halloween_con_top for place {place} with score {score}",
                label="🎃  Halloween Con Top DB",
            ),
            upsert_halloween_con_top_cache(place, score)

    except Exception as e:
        pretty_log("warn", f"Failed to upsert halloween_con_top for place {place}: {e}")


# Get a place's score
async def get_halloween_con_top(bot, place: str):
    try:
        async with bot.pg_pool.acquire() as conn:
            row = await conn.fetchrow(
                "SELECT * FROM halloween_con_top WHERE place = $1", place
            )
            return dict(row) if row else None
    except Exception as e:
        pretty_log("warn", f"Failed to fetch halloween_con_top for place {place}: {e}")
        return None


# Get all places and scores, ordered by score descending
async def get_all_halloween_con_top(bot):
    try:
        async with bot.pg_pool.acquire() as conn:
            rows = await conn.fetch(
                "SELECT * FROM halloween_con_top ORDER BY score DESC"
            )
            return [dict(row) for row in rows]
    except Exception as e:
        pretty_log("warn", f"Failed to fetch all halloween_con_top: {e}")
        return []


# Remove a place
async def remove_halloween_con_top(bot, place: str):
    try:
        async with bot.pg_pool.acquire() as conn:
            await conn.execute("DELETE FROM halloween_con_top WHERE place = $1", place)
            from utils.cache.halloween_con_top_cache import (
                remove_halloween_con_top_cache,
            )

            pretty_log(
                "db",
                f"Removed halloween_con_top for place {place}",
                label="🎃  Halloween Con Top DB",
            )
            # remove from cache too
            remove_halloween_con_top_cache(place)

    except Exception as e:
        pretty_log("warn", f"Failed to remove halloween_con_top for place {place}: {e}")


async def clear_halloween_con_top(bot):
    try:
        async with bot.pg_pool.acquire() as conn:
            await conn.execute("DELETE FROM halloween_con_top")
            from utils.cache.halloween_con_top_cache import halloween_con_top_cache

            halloween_con_top_cache.clear()
            pretty_log(
                "db",
                "Cleared all rows from halloween_con_top table and cache.",
                label="🎃  Halloween Con Top DB",
            )
    except Exception as e:
        pretty_log("warn", f"Failed to clear halloween_con_top table: {e}")
