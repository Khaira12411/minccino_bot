from utils.loggers.pretty_logs import pretty_log

# 💠────────────────────────────────────────────
# [📜 FETCH] All Straymons Members
# 💠────────────────────────────────────────────
async def fetch_all_straymon_members(bot):
    """
    Fetch all Straymons members from the database.
    Returns a list of asyncpg.Record objects, or an empty list if none found.
    """
    try:
        async with bot.pg_pool.acquire() as conn:
            rows = await conn.fetch("SELECT * FROM straymons_members ORDER BY user_id;")

        # 🩵 Log + Return

        pretty_log(
            "db", f"Fetched {len(rows)} straymons_members.", 
        )
        return rows

    except Exception as e:

        pretty_log(
            "error", f"Failed to fetch straymons_members: {e}",
        )
        return []
